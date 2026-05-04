"use client";

import { DetailModalShell } from "@/components/workspace/molecules/detail-modal-shell";
import { CandidateDetailContent } from "@/components/workspace/organisms/detail/candidate-detail-content";
import { PASetupDetailContent } from "@/components/workspace/organisms/detail/pa-setup-detail-content";
import type { CandidateDetail, PASetup } from "@/lib/api";
import type { Locale } from "@/lib/i18n-config";
import { useAppI18n } from "@/lib/use-app-i18n";

export function CandidateDetailPanel({
  detail,
  loading,
  error,
  locale,
  selected,
  onClose
}: {
  detail: CandidateDetail | undefined;
  loading: boolean;
  error: boolean;
  locale: Locale;
  selected: boolean;
  onClose: () => void;
}) {
  const { t } = useAppI18n();
  const candidate = detail?.candidate;
  const setup = detail?.pa_setup;
  const title = candidate ? `${candidate.symbol_id} ${t("candidateDetail")}` : t("candidateDetail");
  const subtitle = setup?.setup_id ?? candidate?.candidate_id ?? t("noSelection");

  return (
    <DetailModalShell
      closeLabel={t("closeDetail")}
      onClose={onClose}
      subtitle={subtitle}
      title={title}
    >
      <CandidateDetailContent
        detail={detail}
        error={error}
        loading={loading}
        locale={locale}
        selected={selected}
      />
    </DetailModalShell>
  );
}

export function PASetupDetailPanel({
  setup,
  locale,
  onClose
}: {
  setup: PASetup | null;
  locale: Locale;
  onClose?: () => void;
}) {
  const { t } = useAppI18n();
  const title = setup ? `${setup.symbol_id} ${t("setupDetail")}` : t("setupDetail");
  const subtitle = setup?.setup_id ?? t("noSelection");

  return (
    <DetailModalShell
      closeLabel={t("closeDetail")}
      onClose={onClose}
      subtitle={subtitle}
      title={title}
    >
      <PASetupDetailContent locale={locale} setup={setup} />
    </DetailModalShell>
  );
}
