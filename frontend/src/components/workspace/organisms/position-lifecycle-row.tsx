"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Loader2, PencilLine, Scissors, XCircle } from "lucide-react";
import { Fragment, useState } from "react";

import {
  ActionPanel,
  DateInput,
  NumberInput,
  TextInput,
  dangerButton,
  datetimeLocalValue,
  isoDatetime,
  optionalPositiveNumber,
  positiveNumber,
  secondaryButton
} from "@/components/workspace/organisms/position-lifecycle/action-panel";
import type { Position } from "@/lib/api";
import { api } from "@/lib/api";
import { formatValue } from "@/lib/format";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

type ActionMode = "activate" | "stop" | "reduce" | "close";

type PositionLifecycleRowProps = {
  locale: Locale;
  position: Position;
};

export function PositionLifecycleRow({ locale, position }: PositionLifecycleRowProps) {
  const { labelFor, t } = useAppI18n();
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<ActionMode | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activationForm, setActivationForm] = useState({
    entryDate: datetimeLocalValue(new Date()),
    entryPrice: "",
    quantity: ""
  });
  const [stopForm, setStopForm] = useState({ newStop: "" });
  const [reduceForm, setReduceForm] = useState({
    currentStop: "",
    exitDate: datetimeLocalValue(new Date()),
    exitPrice: "",
    notes: "",
    quantity: ""
  });
  const [closeForm, setCloseForm] = useState({
    exitDate: datetimeLocalValue(new Date()),
    exitPrice: "",
    exitReason: "manual_review",
    notes: ""
  });

  const invalidateLifecycle = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["positions"] }),
      queryClient.invalidateQueries({ queryKey: ["positions-count"] }),
      queryClient.invalidateQueries({ queryKey: ["portfolio-risk"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["alerts"] }),
      queryClient.invalidateQueries({ queryKey: ["alerts-count"] }),
      queryClient.invalidateQueries({ queryKey: ["journal"] }),
      queryClient.invalidateQueries({ queryKey: ["journal-count"] })
    ]);
  };

  const activatePosition = useMutation({
    mutationFn: (request: { entryDate?: string; entryPrice: number; quantity?: number }) =>
      api.activatePosition(position.position_id, {
        entry_date: request.entryDate,
        entry_price: request.entryPrice,
        quantity: request.quantity
      }),
    onSuccess: async () => {
      setSuccessMessage(t("positionEntryRecorded"));
      setMode(null);
      await invalidateLifecycle();
    }
  });

  const updateStop = useMutation({
    mutationFn: (newStop: number) => api.updatePositionStop(position.position_id, { new_stop: newStop }),
    onSuccess: async () => {
      setSuccessMessage(t("positionStopUpdated"));
      setMode(null);
      await invalidateLifecycle();
    }
  });

  const reducePosition = useMutation({
    mutationFn: (request: {
      currentStop?: number;
      exitDate?: string;
      exitPrice: number;
      notes?: string;
      quantity?: number;
    }) =>
      api.reducePosition(position.position_id, {
        current_stop: request.currentStop,
        exit_date: request.exitDate,
        exit_price: request.exitPrice,
        notes: request.notes,
        quantity: request.quantity
      }),
    onSuccess: async () => {
      setSuccessMessage(t("positionTrimRecorded"));
      setMode(null);
      await invalidateLifecycle();
    }
  });

  const closePosition = useMutation({
    mutationFn: (request: { exitDate?: string; exitPrice: number; exitReason?: string; notes?: string }) =>
      api.closePosition(position.position_id, {
        exit_date: request.exitDate,
        exit_price: request.exitPrice,
        exit_reason: request.exitReason,
        notes: request.notes
      }),
    onSuccess: async () => {
      setSuccessMessage(t("positionClosedRecorded"));
      setMode(null);
      await invalidateLifecycle();
    }
  });

  const cancelPosition = useMutation({
    mutationFn: () => api.cancelPosition(position.position_id),
    onSuccess: async () => {
      setSuccessMessage(t("positionPlanCancelled"));
      setMode(null);
      await invalidateLifecycle();
    }
  });

  const busy =
    activatePosition.isPending ||
    updateStop.isPending ||
    reducePosition.isPending ||
    closePosition.isPending ||
    cancelPosition.isPending;
  const failed =
    activatePosition.isError ||
    updateStop.isError ||
    reducePosition.isError ||
    closePosition.isError ||
    cancelPosition.isError;
  const canManageStop = position.status === "planned" || position.status === "open" || position.status === "reduce";
  const canManageActive = position.status === "open" || position.status === "reduce";
  const hasActions = position.status === "planned" || canManageStop || canManageActive;

  const openMode = (nextMode: ActionMode) => {
    setMode((current) => (current === nextMode ? null : nextMode));
    setSuccessMessage(null);
    activatePosition.reset();
    updateStop.reset();
    reducePosition.reset();
    closePosition.reset();
    cancelPosition.reset();
    if (nextMode === "activate") {
      setActivationForm({
        entryDate: position.entry_date ? datetimeLocalValue(new Date(position.entry_date)) : datetimeLocalValue(new Date()),
        entryPrice: String(position.entry_price ?? ""),
        quantity: position.quantity === null ? "" : String(position.quantity)
      });
    }
    if (nextMode === "stop") {
      setStopForm({ newStop: String(position.current_stop ?? position.initial_stop ?? "") });
    }
    if (nextMode === "reduce") {
      setReduceForm({
        currentStop: String(position.current_stop ?? ""),
        exitDate: datetimeLocalValue(new Date()),
        exitPrice: "",
        notes: "",
        quantity: ""
      });
    }
    if (nextMode === "close") {
      setCloseForm({
        exitDate: datetimeLocalValue(new Date()),
        exitPrice: "",
        exitReason: "manual_review",
        notes: ""
      });
    }
  };

  const submitActivation = () => {
    const entryPrice = positiveNumber(activationForm.entryPrice);
    const quantity = optionalPositiveNumber(activationForm.quantity);
    if (entryPrice === null || quantity === null) {
      return;
    }
    activatePosition.mutate({
      entryDate: isoDatetime(activationForm.entryDate),
      entryPrice,
      quantity
    });
  };

  const submitStop = () => {
    const newStop = positiveNumber(stopForm.newStop);
    if (newStop === null) {
      return;
    }
    updateStop.mutate(newStop);
  };

  const submitReduce = () => {
    const exitPrice = positiveNumber(reduceForm.exitPrice);
    const quantity = optionalPositiveNumber(reduceForm.quantity);
    const currentStop = optionalPositiveNumber(reduceForm.currentStop);
    if (exitPrice === null || quantity === null || quantity === undefined || currentStop === null) {
      return;
    }
    reducePosition.mutate({
      currentStop,
      exitDate: isoDatetime(reduceForm.exitDate),
      exitPrice,
      notes: reduceForm.notes || undefined,
      quantity
    });
  };

  const submitClose = () => {
    const exitPrice = positiveNumber(closeForm.exitPrice);
    if (exitPrice === null) {
      return;
    }
    closePosition.mutate({
      exitDate: isoDatetime(closeForm.exitDate),
      exitPrice,
      exitReason: closeForm.exitReason || undefined,
      notes: closeForm.notes || undefined
    });
  };

  const submitCancelPlan = () => {
    cancelPosition.reset();
    if (!window.confirm(t("cancelPlanConfirm"))) {
      return;
    }
    cancelPosition.mutate();
  };

  return (
    <Fragment>
      <tr className="border-t border-line">
        <td className="px-4 py-3 font-medium text-ink">{position.symbol_id}</td>
        <td className="px-4 py-3">{position.asset_type}</td>
        <td className="px-4 py-3">{formatValue(position.quantity)}</td>
        <td className="px-4 py-3">{formatValue(position.entry_price)}</td>
        <td className="px-4 py-3">{formatValue(position.current_stop)}</td>
        <td className="px-4 py-3">{formatValue(position.risk_amount)}</td>
        <td className="px-4 py-3">{formatPercent(position.risk_pct)}</td>
        <td className="px-4 py-3">
          <div className="font-medium text-ink">{labelFor("status", position.status)}</div>
          {position.exit_profile ? (
            <div className="mt-1 text-xs font-semibold text-teal">{labelFor("plan", position.exit_profile)}</div>
          ) : null}
          <div className="mt-1 max-w-56 text-xs leading-5 text-slate-500">{nextStepText(position.status, t)}</div>
        </td>
        <td className="px-4 py-3">
          <div className="flex flex-wrap gap-2">
            {position.status === "planned" ? (
              <button className={secondaryButton} disabled={busy} onClick={() => openMode("activate")} type="button">
                <CheckCircle2 size={14} />
                {t("markEntry")}
              </button>
            ) : null}
            {canManageStop ? (
              <button className={secondaryButton} disabled={busy} onClick={() => openMode("stop")} type="button">
                <PencilLine size={14} />
                {t("updateStop")}
              </button>
            ) : null}
            {position.status === "planned" ? (
              <button className={dangerButton} disabled={busy} onClick={submitCancelPlan} type="button">
                {cancelPosition.isPending ? <Loader2 className="animate-spin" size={14} /> : <XCircle size={14} />}
                {t("cancelPlan")}
              </button>
            ) : null}
            {canManageActive ? (
              <button className={secondaryButton} disabled={busy} onClick={() => openMode("reduce")} type="button">
                <Scissors size={14} />
                {t("markTrim")}
              </button>
            ) : null}
            {canManageActive ? (
              <button className={dangerButton} disabled={busy} onClick={() => openMode("close")} type="button">
                <XCircle size={14} />
                {t("closePosition")}
              </button>
            ) : null}
            {!hasActions ? <span className="text-slate-400">-</span> : null}
          </div>
          {successMessage ? (
            <p className="mt-2 rounded-md border border-teal-200 bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800">
              {successMessage}
            </p>
          ) : null}
        </td>
      </tr>
      {mode ? (
        <tr className="border-t border-line bg-teal-50/35">
          <td className="px-4 py-4" colSpan={9}>
            {mode === "activate" ? (
              <ActionPanel
                busy={busy}
                description={t("markEntryHelp")}
                failed={failed}
                onCancel={() => setMode(null)}
                onSubmit={submitActivation}
                submitLabel={t("confirmEntry")}
                title={t("markEntryTitle")}
                t={t}
              >
                <NumberInput
                  label={t("actualEntry")}
                  onChange={(entryPrice) => setActivationForm((value) => ({ ...value, entryPrice }))}
                  value={activationForm.entryPrice}
                />
                <NumberInput
                  label={t("qty")}
                  onChange={(quantity) => setActivationForm((value) => ({ ...value, quantity }))}
                  value={activationForm.quantity}
                />
                <DateInput
                  label={t("entryTime")}
                  onChange={(entryDate) => setActivationForm((value) => ({ ...value, entryDate }))}
                  value={activationForm.entryDate}
                />
              </ActionPanel>
            ) : null}
            {mode === "stop" ? (
              <ActionPanel
                busy={busy}
                description={t("updateStopHelp")}
                failed={failed}
                onCancel={() => setMode(null)}
                onSubmit={submitStop}
                submitLabel={t("confirmStop")}
                title={t("updateStopTitle")}
                t={t}
              >
                <NumberInput
                  label={t("newStop")}
                  onChange={(newStop) => setStopForm({ newStop })}
                  value={stopForm.newStop}
                />
              </ActionPanel>
            ) : null}
            {mode === "reduce" ? (
              <ActionPanel
                busy={busy}
                description={t("markTrimHelp")}
                failed={failed}
                onCancel={() => setMode(null)}
                onSubmit={submitReduce}
                submitLabel={t("confirmTrim")}
                title={t("markTrimTitle")}
                t={t}
              >
                <NumberInput
                  label={t("trimPrice")}
                  onChange={(exitPrice) => setReduceForm((value) => ({ ...value, exitPrice }))}
                  value={reduceForm.exitPrice}
                />
                <NumberInput
                  label={t("trimQty")}
                  onChange={(quantity) => setReduceForm((value) => ({ ...value, quantity }))}
                  value={reduceForm.quantity}
                />
                <NumberInput
                  label={t("newStop")}
                  onChange={(currentStop) => setReduceForm((value) => ({ ...value, currentStop }))}
                  value={reduceForm.currentStop}
                />
                <DateInput
                  label={t("exitTime")}
                  onChange={(exitDate) => setReduceForm((value) => ({ ...value, exitDate }))}
                  value={reduceForm.exitDate}
                />
              </ActionPanel>
            ) : null}
            {mode === "close" ? (
              <ActionPanel
                busy={busy}
                description={t("closePositionHelp")}
                failed={failed}
                onCancel={() => setMode(null)}
                onSubmit={submitClose}
                submitLabel={t("confirmClose")}
                title={t("closePositionTitle")}
                t={t}
              >
                <NumberInput
                  label={t("exitPrice")}
                  onChange={(exitPrice) => setCloseForm((value) => ({ ...value, exitPrice }))}
                  value={closeForm.exitPrice}
                />
                <DateInput
                  label={t("exitTime")}
                  onChange={(exitDate) => setCloseForm((value) => ({ ...value, exitDate }))}
                  value={closeForm.exitDate}
                />
                <TextInput
                  label={t("exitReason")}
                  onChange={(exitReason) => setCloseForm((value) => ({ ...value, exitReason }))}
                  value={closeForm.exitReason}
                />
                <TextInput
                  label={t("notes")}
                  onChange={(notes) => setCloseForm((value) => ({ ...value, notes }))}
                  value={closeForm.notes}
                />
              </ActionPanel>
            ) : null}
          </td>
        </tr>
      ) : null}
    </Fragment>
  );
}

function nextStepText(status: string | null, t: ReturnType<typeof useAppI18n>["t"]) {
  if (status === "planned") {
    return t("positionNextStepPlanned");
  }
  if (status === "open") {
    return t("positionNextStepOpen");
  }
  if (status === "reduce") {
    return t("positionNextStepReduce");
  }
  if (status === "closed") {
    return t("positionNextStepClosed");
  }
  if (status === "cancelled") {
    return t("positionNextStepCancelled");
  }
  if (status === "review_needed") {
    return t("positionNextStepReviewNeeded");
  }
  return t("positionNextStepUnknown");
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "-";
  }
  return `${(value * 100).toFixed(2)}%`;
}
