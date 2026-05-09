from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import AutomationJobRunRequest, JobRun
from backend.app.services.job_run_service import JobRunService


class BusinessJobsMixin:
    @staticmethod
    def run_automation_job(
        session: Session,
        principal: AuthPrincipal,
        request: AutomationJobRunRequest,
    ) -> JobRun:
        return JobRunService.run_automation_job(session, principal, request)

    @staticmethod
    def _complete_job_run(
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
        return JobRunService.complete_job_run(
            session=session,
            principal=principal,
            run_id=run_id,
            started_at=started_at,
            status=status,
            records_written=records_written,
            steps=steps,
            request=request,
            error_message=error_message,
        )

    @staticmethod
    def list_job_runs(
        session: Session,
        principal: AuthPrincipal,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JobRun]:
        return JobRunService.list_job_runs(
            session,
            principal,
            status=status,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def count_job_runs(
        session: Session,
        principal: AuthPrincipal,
        *,
        status: str | None = None,
    ) -> int:
        return JobRunService.count_job_runs(session, principal, status=status)

    @staticmethod
    def _job_runs_statement(
        *,
        principal: AuthPrincipal,
        status: str | None = None,
    ):
        return JobRunService.job_runs_statement(principal=principal, status=status)
