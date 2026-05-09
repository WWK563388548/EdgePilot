from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    AutomationJobRunRequest,
    ExitAlertEvaluationRequest,
    JobRun,
)
from backend.app.schemas.ingestion import AccountETFUniverseRefreshRequest
from backend.app.schemas.outcome import ScannerOutcomeRecalculateRequest
from backend.app.schemas.pa import AccountETFRotationScannerRequest, AccountETFOneilScannerRequest
from backend.app.services.audit_service import AuditService
from backend.app.services.data_source_service import DataSourceService

ONEIL_CORE_US_ETF_STRATEGY = "oneil_core_us_etf"
ETF_ROTATION_US_ETF_STRATEGY = "etf_rotation_us_etf"


class JobRunService:
    @staticmethod
    def run_automation_job(
        session: Session,
        principal: AuthPrincipal,
        request: AutomationJobRunRequest,
    ) -> JobRun:
        from backend.app.services.business_service import BusinessService

        started_at = datetime.now(UTC)
        run_id = f"job_{uuid4().hex}"
        job = db.JobRun(
            run_id=run_id,
            account_id=principal.account_id,
            job_type="market_refresh_scan",
            status="running",
            trigger="manual",
            records_written=0,
            metadata_json={"steps": [], "request": request.model_dump(mode="json")},
            started_at=started_at,
        )
        session.add(job)
        session.flush()

        steps: list[dict[str, Any]] = []
        records_written = 0
        strategy_name = request.strategy_name or ETF_ROTATION_US_ETF_STRATEGY
        if strategy_name not in {ETF_ROTATION_US_ETF_STRATEGY, ONEIL_CORE_US_ETF_STRATEGY}:
            strategy_name = ONEIL_CORE_US_ETF_STRATEGY
        refresh_step_name = (
            "etf_rotation_refresh_scan"
            if strategy_name == ETF_ROTATION_US_ETF_STRATEGY
            else "market_refresh_scan"
        )
        scan_step_name = (
            "etf_rotation_scan"
            if strategy_name == ETF_ROTATION_US_ETF_STRATEGY
            else "oneil_core_scan"
        )
        try:
            if request.refresh_market_data:
                refresh_request = AccountETFUniverseRefreshRequest(
                    symbols=request.symbols,
                    min_score=request.min_score,
                    max_candidates=request.max_candidates,
                )
                if strategy_name == ETF_ROTATION_US_ETF_STRATEGY:
                    refresh_response = BusinessService.refresh_account_etf_rotation_universe(
                        session,
                        principal,
                        refresh_request,
                    )
                    step_name = refresh_step_name
                else:
                    refresh_response = BusinessService.refresh_account_oneil_core_universe(
                        session,
                        principal,
                        refresh_request,
                    )
                    step_name = refresh_step_name
                records_written += (
                    refresh_response.bars_written
                    + refresh_response.facts_written
                    + refresh_response.setups_written
                    + refresh_response.candidates_written
                )
                symbols_succeeded = sum(
                    1 for row in refresh_response.symbol_results if row.status == "success"
                )
                symbols_failed = len(refresh_response.symbol_results) - symbols_succeeded
                error_summary = "; ".join(
                    f"{row.symbol}: {row.error_message}"
                    for row in refresh_response.symbol_results
                    if row.status != "success" and row.error_message
                )
                capability = DataSourceService.record_polygon_refresh_result(
                    session,
                    principal.tenant_id,
                    success_count=symbols_succeeded,
                    failure_count=symbols_failed,
                    error_summary=error_summary or None,
                )
                steps.append(
                    {
                        "name": step_name,
                        "status": "succeeded",
                        "summary": {
                            "strategy_name": strategy_name,
                            "bars_written": refresh_response.bars_written,
                            "facts_written": refresh_response.facts_written,
                            "setups_written": refresh_response.setups_written,
                            "candidates_written": refresh_response.candidates_written,
                            "decision_counts": refresh_response.decision_counts,
                            "latest_scan_date": refresh_response.latest_scan_date.isoformat()
                            if refresh_response.latest_scan_date
                            else None,
                            "latest_bar_date": refresh_response.latest_bar_date.isoformat()
                            if refresh_response.latest_bar_date
                            else None,
                            "data_source": {
                                "provider": "polygon",
                                "capability_key": capability.capability_key,
                                "status": capability.status,
                                "source": capability.source,
                            },
                            "symbols_requested": refresh_response.symbols_requested,
                            "symbols_succeeded": symbols_succeeded,
                            "symbols_failed": symbols_failed,
                            "error_summary": error_summary or None,
                        },
                    }
                )
            else:
                if strategy_name == ETF_ROTATION_US_ETF_STRATEGY:
                    scanner_response = BusinessService.run_account_etf_rotation_scanner(
                        session,
                        principal,
                        AccountETFRotationScannerRequest(
                            symbols=request.symbols,
                            min_score=request.min_score,
                            max_candidates=request.max_candidates,
                            recalculate_facts=True,
                        ),
                    )
                    step_name = scan_step_name
                else:
                    scanner_response = BusinessService.run_account_oneil_core_scanner(
                        session,
                        principal,
                        AccountETFOneilScannerRequest(
                            symbols=request.symbols,
                            min_score=request.min_score,
                            max_candidates=request.max_candidates,
                            recalculate_facts=True,
                        ),
                    )
                    step_name = scan_step_name
                records_written += (
                    scanner_response.facts_written
                    + scanner_response.setups_written
                    + scanner_response.candidates_written
                )
                steps.append(
                    {
                        "name": step_name,
                        "status": "succeeded",
                        "summary": {
                            "strategy_name": strategy_name,
                            "facts_written": scanner_response.facts_written,
                            "setups_written": scanner_response.setups_written,
                            "candidates_written": scanner_response.candidates_written,
                            "decision_counts": scanner_response.decision_counts,
                            "latest_scan_date": scanner_response.latest_scan_date.isoformat()
                            if scanner_response.latest_scan_date
                            else None,
                            "latest_bar_date": scanner_response.latest_bar_date.isoformat()
                            if scanner_response.latest_bar_date
                            else None,
                        },
                    }
                )

            if request.recalculate_outcomes:
                outcome_response = BusinessService.recalculate_scanner_outcomes(
                    session,
                    principal,
                    ScannerOutcomeRecalculateRequest(
                        strategy_name=strategy_name,
                        limit=request.outcome_limit,
                    ),
                )
                records_written += outcome_response.outcomes_written
                steps.append(
                    {
                        "name": "scanner_outcomes",
                        "status": "succeeded",
                        "summary": {
                            "candidates_scanned": outcome_response.candidates_scanned,
                            "outcomes_written": outcome_response.outcomes_written,
                            "skipped_candidates": outcome_response.skipped_candidates,
                            "status_counts": outcome_response.status_counts,
                        },
                    }
                )

            if request.evaluate_alerts:
                alert_response = BusinessService.evaluate_exit_alerts(
                    session,
                    principal,
                    ExitAlertEvaluationRequest(limit=request.alert_limit),
                )
                records_written += alert_response.alerts_created
                steps.append(
                    {
                        "name": "exit_alerts",
                        "status": "succeeded",
                        "summary": {
                            "positions_evaluated": alert_response.positions_evaluated,
                            "alerts_created": alert_response.alerts_created,
                            "skipped_positions": alert_response.skipped_positions,
                            "duplicate_alerts": alert_response.duplicate_alerts,
                        },
                    }
                )

            return JobRunService.complete_job_run(
                session=session,
                principal=principal,
                run_id=run_id,
                started_at=started_at,
                status="succeeded",
                records_written=records_written,
                steps=steps,
                request=request,
            )
        except Exception as exc:
            session.rollback()
            if not steps or steps[-1].get("status") != "failed":
                steps.append(
                    {
                        "name": refresh_step_name
                        if request.refresh_market_data
                        else scan_step_name,
                        "status": "failed",
                        "summary": {
                            "error": str(exc),
                            "symbols_requested": request.symbols or [],
                        },
                    }
                )
            return JobRunService.complete_job_run(
                session=session,
                principal=principal,
                run_id=run_id,
                started_at=started_at,
                status="failed",
                records_written=records_written,
                steps=steps,
                request=request,
                error_message=str(exc),
            )

    @staticmethod
    def complete_job_run(
        *,
        session: Session,
        principal: AuthPrincipal,
        run_id: str,
        started_at: datetime,
        status: str,
        records_written: int,
        steps: list[dict[str, Any]],
        request: AutomationJobRunRequest,
        error_message: str | None = None,
    ) -> JobRun:
        completed_at = datetime.now(UTC)
        job = session.get(db.JobRun, run_id)
        if job is None:
            job = db.JobRun(
                run_id=run_id,
                account_id=principal.account_id,
                job_type="market_refresh_scan",
                trigger="manual",
                started_at=started_at,
            )
            session.add(job)
        job.status = status
        job.records_written = records_written
        job.error_message = error_message
        job.completed_at = completed_at
        job.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        job.metadata_json = {
            "steps": steps,
            "request": request.model_dump(mode="json"),
        }
        AuditService.record(session, principal, "job.run", "job_run", run_id)
        session.commit()
        session.refresh(job)
        return JobRun.model_validate(job)

    @staticmethod
    def list_job_runs(
        session: Session,
        principal: AuthPrincipal,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobRun]:
        statement = JobRunService.job_runs_statement(principal=principal, status=status)
        statement = statement.order_by(db.JobRun.started_at.desc()).limit(limit).offset(offset)
        return [JobRun.model_validate(row) for row in session.scalars(statement).all()]

    @staticmethod
    def count_job_runs(
        session: Session,
        principal: AuthPrincipal,
        *,
        status: str | None = None,
    ) -> int:
        statement = JobRunService.job_runs_statement(principal=principal, status=status)
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def job_runs_statement(
        *,
        principal: AuthPrincipal,
        status: str | None = None,
    ):
        statement = select(db.JobRun).where(db.JobRun.account_id == principal.account_id)
        if status:
            statement = statement.where(db.JobRun.status == status)
        return statement
