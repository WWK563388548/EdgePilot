"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { TableShell } from "@/components/workspace/molecules/table-shell";
import {
  ExecutionImportForm,
  ExecutionImportSubmitButton
} from "@/components/workspace/organisms/execution-import/execution-import-form";
import {
  ExecutionFillsTable,
  ExecutionImportsTable,
  ReviewNeededPanel
} from "@/components/workspace/organisms/execution-import/execution-import-tables";
import { api, type ExecutionFillReconcileRequest, type ExecutionImportResult } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

const EXECUTION_PAGE_SIZE = 8;

export function ExecutionImportView({ locale }: { locale: Locale }) {
  const { t } = useAppI18n();
  const queryClient = useQueryClient();
  const [broker, setBroker] = useState("edgepilot_generic_csv");
  const [sourceFilename, setSourceFilename] = useState("");
  const [csvText, setCsvText] = useState("");
  const [result, setResult] = useState<ExecutionImportResult | null>(null);
  const [importPage, setImportPage] = useState(0);
  const [fillPage, setFillPage] = useState(0);

  const imports = useQuery({
    queryKey: ["execution-imports", importPage],
    queryFn: () =>
      api.executionImports({
        limit: EXECUTION_PAGE_SIZE + 1,
        offset: importPage * EXECUTION_PAGE_SIZE
      })
  });
  const importsCount = useQuery({
    queryKey: ["execution-imports-count"],
    queryFn: () => api.executionImportsCount()
  });
  const fills = useQuery({
    queryKey: ["execution-fills", fillPage],
    queryFn: () =>
      api.executionFills({
        limit: EXECUTION_PAGE_SIZE + 1,
        offset: fillPage * EXECUTION_PAGE_SIZE
      })
  });
  const fillsCount = useQuery({
    queryKey: ["execution-fills-count"],
    queryFn: () => api.executionFillsCount()
  });
  const reviewNeeded = useQuery({
    queryKey: ["execution-fills", "review_needed", 0],
    queryFn: () =>
      api.executionFills({
        limit: 5,
        offset: 0,
        reconciliationStatus: "review_needed",
        status: "active"
      })
  });
  const reviewNeededCount = useQuery({
    queryKey: ["execution-fills-count", "review_needed"],
    queryFn: () =>
      api.executionFillsCount({
        reconciliationStatus: "review_needed",
        status: "active"
      })
  });

  const importCsv = useMutation({
    mutationFn: () =>
      api.importExecutionCsv({
        broker: broker.trim() || "edgepilot_generic_csv",
        csv_text: csvText,
        source_filename: sourceFilename.trim() || null
      }),
    onSuccess: async (response) => {
      setResult(response);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["execution-imports"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-imports-count"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-fills"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-fills-count"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });

  const reconcileFill = useMutation({
    mutationFn: ({ fillId, request }: { fillId: string; request: ExecutionFillReconcileRequest }) =>
      api.reconcileExecutionFill(fillId, request),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["execution-fills"] }),
        queryClient.invalidateQueries({ queryKey: ["execution-fills-count"] }),
        queryClient.invalidateQueries({ queryKey: ["positions"] }),
        queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] })
      ]);
    }
  });

  const importRows = (imports.data ?? []).slice(0, EXECUTION_PAGE_SIZE);
  const fillRows = (fills.data ?? []).slice(0, EXECUTION_PAGE_SIZE);
  const hasImportNext =
    importsCount.data?.total !== undefined
      ? (importPage + 1) * EXECUTION_PAGE_SIZE < importsCount.data.total
      : (imports.data ?? []).length > EXECUTION_PAGE_SIZE;
  const hasFillNext =
    fillsCount.data?.total !== undefined
      ? (fillPage + 1) * EXECUTION_PAGE_SIZE < fillsCount.data.total
      : (fills.data ?? []).length > EXECUTION_PAGE_SIZE;
  const canImport = csvText.trim().length > 0 && !importCsv.isPending;

  return (
    <div className="grid gap-5">
      <TableShell
        title={t("executionImport")}
        loading={importCsv.isPending}
        error={importCsv.isError}
        locale={locale}
        actions={
          <ExecutionImportSubmitButton
            canImport={canImport}
            importing={importCsv.isPending}
            onSubmit={() => importCsv.mutate()}
          />
        }
      >
        <ExecutionImportForm
          broker={broker}
          csvText={csvText}
          importError={importCsv.isError}
          locale={locale}
          onBrokerChange={setBroker}
          onCsvTextChange={setCsvText}
          onSourceFilenameChange={setSourceFilename}
          result={result}
          sourceFilename={sourceFilename}
        />
      </TableShell>

      <ReviewNeededPanel
        data={reviewNeeded.data ?? []}
        error={reviewNeeded.isError || reviewNeededCount.isError}
        loading={reviewNeeded.isLoading || reviewNeededCount.isLoading}
        locale={locale}
        onReconcile={(fillId, request) => reconcileFill.mutate({ fillId, request })}
        reconcilingFillId={reconcileFill.isPending ? reconcileFill.variables?.fillId : undefined}
        reconcileError={reconcileFill.isError}
        totalCount={reviewNeededCount.data?.total}
      />

      <ExecutionImportsTable
        data={importRows}
        error={imports.isError}
        hasNextPage={hasImportNext}
        loading={imports.isLoading}
        locale={locale}
        onPageChange={setImportPage}
        page={importPage}
        totalCount={importsCount.data?.total}
      />

      <ExecutionFillsTable
        data={fillRows}
        error={fills.isError}
        hasNextPage={hasFillNext}
        loading={fills.isLoading}
        locale={locale}
        onPageChange={setFillPage}
        page={fillPage}
        totalCount={fillsCount.data?.total}
      />
    </div>
  );
}
