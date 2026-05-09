from __future__ import annotations

from collections import Counter

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.ingestion import (
    AccountETFUniverseRefreshRequest,
    ETFUniverseSeedRequest,
    ETFUniverseSeedResponse,
)
from backend.app.schemas.outcome import (
    ScannerOutcome,
    ScannerOutcomeRecalculateRequest,
    ScannerOutcomeRecalculateResponse,
    ScannerOutcomeSummary,
)
from backend.app.schemas.pa import (
    AccountETFRotationScannerRequest,
    AccountETFOneilScannerRequest,
    ETFRotationScannerRequest,
    ETFOneilScannerRequest,
    ETFOneilScannerResponse,
)
from backend.app.services.data_source_service import DataSourceService
from backend.app.services.etf_seed_service import ETFSeedService
from backend.app.services.scanner_outcome_service import ScannerOutcomeService
from backend.app.services.scanner_service import ETFScannerService
from backend.app.services.scanners.common import (
    ETF_ROTATION_US_ETF_STRATEGY,
    ONEIL_CORE_US_ETF_STRATEGY,
)

ETF_ROTATION_DEFAULT_BENCHMARK_SYMBOL = "SPY"


def _average(values) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 6)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


class BusinessScannersMixin:
    @classmethod
    def run_account_oneil_core_scanner(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFOneilScannerRequest,
    ) -> ETFOneilScannerResponse:
        cls._delete_account_strategy_candidates_and_outcomes(
            session,
            principal,
            ONEIL_CORE_US_ETF_STRATEGY,
        )
        response = ETFScannerService.run_us_etf_oneil_core_for_session(
            session,
            ETFOneilScannerRequest(
                symbols=request.symbols,
                timeframe=request.timeframe,
                account_id=principal.account_id,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
                recalculate_facts=request.recalculate_facts,
            ),
        )
        cls._create_notification_event(
            session,
            principal,
            event_type="scanner_candidates_updated",
            severity="info",
            source_type="scanner",
            source_id=None,
            title="Scanner candidates updated",
            body=f"{response.candidates_written} scanner candidates were generated.",
            target_view="candidates",
            target_id=None,
            metadata_json={
                "strategy_name": ONEIL_CORE_US_ETF_STRATEGY,
                "candidates_written": response.candidates_written,
                "decision_counts": response.decision_counts,
                "latest_scan_date": response.latest_scan_date.isoformat()
                if response.latest_scan_date
                else None,
                "source": "manual_scan",
            },
        )
        cls._audit(
            session,
            principal,
            "candidate.scan",
            "scanner",
            ONEIL_CORE_US_ETF_STRATEGY,
        )
        session.commit()
        return response

    @classmethod
    def run_account_etf_rotation_scanner(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFRotationScannerRequest,
    ) -> ETFOneilScannerResponse:
        cls._delete_account_strategy_candidates_and_outcomes(
            session,
            principal,
            ETF_ROTATION_US_ETF_STRATEGY,
        )
        response = ETFScannerService.run_us_etf_rotation_for_session(
            session,
            ETFRotationScannerRequest(
                symbols=request.symbols,
                timeframe=request.timeframe,
                account_id=principal.account_id,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
                recalculate_facts=request.recalculate_facts,
                benchmark_symbol=request.benchmark_symbol,
            ),
        )
        cls._create_notification_event(
            session,
            principal,
            event_type="scanner_candidates_updated",
            severity="info",
            source_type="scanner",
            source_id=None,
            title="ETF rotation candidates updated",
            body=f"{response.candidates_written} ETF rotation candidates were generated.",
            target_view="candidates",
            target_id=None,
            metadata_json={
                "strategy_name": ETF_ROTATION_US_ETF_STRATEGY,
                "candidates_written": response.candidates_written,
                "decision_counts": response.decision_counts,
                "latest_scan_date": response.latest_scan_date.isoformat()
                if response.latest_scan_date
                else None,
                "source": "manual_scan",
                "benchmark_symbol": request.benchmark_symbol,
            },
        )
        cls._audit(
            session,
            principal,
            "candidate.scan",
            "scanner",
            ETF_ROTATION_US_ETF_STRATEGY,
        )
        session.commit()
        return response

    @classmethod
    def refresh_account_oneil_core_universe(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFUniverseRefreshRequest,
    ) -> ETFUniverseSeedResponse:
        client, data_source = DataSourceService.polygon_client_for_tenant(session, principal)
        cls._delete_account_strategy_candidates_and_outcomes(
            session,
            principal,
            ONEIL_CORE_US_ETF_STRATEGY,
        )
        response = ETFSeedService.seed_us_etf_universe_for_session(
            session=session,
            client=client,
            request=ETFUniverseSeedRequest(
                symbols=request.symbols,
                from_date=request.from_date,
                to_date=request.to_date,
                timeframe=request.timeframe,
                lookback_days=request.lookback_days,
                account_id=principal.account_id,
                run_pa_facts=True,
                run_scanner=True,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
            ),
        )
        success_count = sum(1 for row in response.symbol_results if row.status == "success")
        failure_messages = [
            f"{row.symbol}: {row.error_message}"
            for row in response.symbol_results
            if row.status != "success" and row.error_message
        ]
        DataSourceService.record_polygon_refresh_result(
            session,
            principal.tenant_id,
            success_count=success_count,
            failure_count=len(response.symbol_results) - success_count,
            error_summary="; ".join(failure_messages[:3]) or None,
        )
        cls._create_notification_event(
            session,
            principal,
            event_type="scanner_candidates_updated",
            severity="info",
            source_type="scanner",
            source_id=None,
            title="Scanner candidates updated",
            body=f"{response.candidates_written} scanner candidates were generated after market refresh.",
            target_view="candidates",
            target_id=None,
            metadata_json={
                "strategy_name": ONEIL_CORE_US_ETF_STRATEGY,
                "candidates_written": response.candidates_written,
                "decision_counts": response.decision_counts,
                "latest_scan_date": response.latest_scan_date.isoformat()
                if response.latest_scan_date
                else None,
                "latest_bar_date": response.latest_bar_date.isoformat()
                if response.latest_bar_date
                else None,
                "source": "market_refresh_scan",
                "data_source": data_source.metadata(),
                "symbols_requested": response.symbols_requested,
                "symbols_succeeded": success_count,
                "symbols_failed": len(response.symbol_results) - success_count,
                "error_summary": "; ".join(failure_messages[:3]) or None,
            },
        )
        cls._audit(
            session,
            principal,
            "candidate.refresh_scan",
            "scanner",
            ONEIL_CORE_US_ETF_STRATEGY,
        )
        session.commit()
        return response

    @classmethod
    def refresh_account_etf_rotation_universe(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFUniverseRefreshRequest,
    ) -> ETFUniverseSeedResponse:
        client, data_source = DataSourceService.polygon_client_for_tenant(session, principal)
        cls._delete_account_strategy_candidates_and_outcomes(
            session,
            principal,
            ETF_ROTATION_US_ETF_STRATEGY,
        )
        seed_symbols = request.symbols
        if seed_symbols is not None and ETF_ROTATION_DEFAULT_BENCHMARK_SYMBOL not in seed_symbols:
            seed_symbols = [*seed_symbols, ETF_ROTATION_DEFAULT_BENCHMARK_SYMBOL]
        seed_response = ETFSeedService.seed_us_etf_universe_for_session(
            session=session,
            client=client,
            request=ETFUniverseSeedRequest(
                symbols=seed_symbols,
                from_date=request.from_date,
                to_date=request.to_date,
                timeframe=request.timeframe,
                lookback_days=request.lookback_days,
                account_id=principal.account_id,
                run_pa_facts=True,
                run_scanner=False,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
            ),
        )
        requested_symbol_set = set(request.symbols) if request.symbols is not None else None
        successful_symbols = [
            row.symbol
            for row in seed_response.symbol_results
            if row.status == "success"
            and (requested_symbol_set is None or row.symbol in requested_symbol_set)
        ]
        scanner_response = ETFScannerService.run_us_etf_rotation_for_session(
            session,
            ETFRotationScannerRequest(
                symbols=successful_symbols,
                timeframe=request.timeframe,
                account_id=principal.account_id,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
                recalculate_facts=False,
            ),
        )
        success_count = len(successful_symbols)
        failure_messages = [
            f"{row.symbol}: {row.error_message}"
            for row in seed_response.symbol_results
            if row.status != "success" and row.error_message
        ]
        skipped_symbols = list(seed_response.skipped_symbols)
        for row in seed_response.symbol_results:
            if row.status != "success" and row.symbol not in skipped_symbols:
                skipped_symbols.append(row.symbol)
        for symbol in scanner_response.skipped_symbols:
            if symbol not in skipped_symbols:
                skipped_symbols.append(symbol)
        DataSourceService.record_polygon_refresh_result(
            session,
            principal.tenant_id,
            success_count=success_count,
            failure_count=len(seed_response.symbol_results) - success_count,
            error_summary="; ".join(failure_messages[:3]) or None,
        )
        response = seed_response.model_copy(
            update={
                "facts_written": seed_response.facts_written + scanner_response.facts_written,
                "setups_written": scanner_response.setups_written,
                "candidates_written": scanner_response.candidates_written,
                "decision_counts": scanner_response.decision_counts,
                "latest_scan_date": scanner_response.latest_scan_date,
                "latest_bar_date": scanner_response.latest_bar_date or seed_response.latest_bar_date,
                "skipped_symbols": skipped_symbols,
                "candidates": scanner_response.candidates,
            }
        )
        cls._create_notification_event(
            session,
            principal,
            event_type="scanner_candidates_updated",
            severity="info",
            source_type="scanner",
            source_id=None,
            title="ETF rotation candidates updated",
            body=f"{response.candidates_written} ETF rotation candidates were generated after market refresh.",
            target_view="candidates",
            target_id=None,
            metadata_json={
                "strategy_name": ETF_ROTATION_US_ETF_STRATEGY,
                "candidates_written": response.candidates_written,
                "decision_counts": response.decision_counts,
                "latest_scan_date": response.latest_scan_date.isoformat()
                if response.latest_scan_date
                else None,
                "latest_bar_date": response.latest_bar_date.isoformat()
                if response.latest_bar_date
                else None,
                "source": "market_refresh_scan",
                "data_source": data_source.metadata(),
                "symbols_requested": response.symbols_requested,
                "symbols_succeeded": success_count,
                "symbols_failed": len(seed_response.symbol_results) - success_count,
                "error_summary": "; ".join(failure_messages[:3]) or None,
            },
        )
        cls._audit(
            session,
            principal,
            "candidate.refresh_scan",
            "scanner",
            ETF_ROTATION_US_ETF_STRATEGY,
        )
        session.commit()
        return response

    @classmethod
    def list_scanner_outcomes(
        cls,
        session: Session,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScannerOutcome]:
        statement = cls._scanner_outcome_statement(
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
        rows = session.scalars(
            statement.order_by(db.ScannerOutcome.detected_ts.desc(), db.ScannerOutcome.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [ScannerOutcome.model_validate(row) for row in rows]

    @classmethod
    def count_scanner_outcomes(
        cls,
        session: Session,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
    ) -> int:
        statement = cls._scanner_outcome_statement(
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @classmethod
    def scanner_outcome_summary(
        cls,
        session: Session,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
    ) -> ScannerOutcomeSummary:
        statement = cls._scanner_outcome_statement(
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
        rows = list(session.scalars(statement).all())
        total = len(rows)
        pending_count = sum(row.evaluation_status == "pending" for row in rows)
        matured_count = sum(row.evaluation_status.startswith("matured") for row in rows)
        triggered_count = sum(row.triggered_entry is True for row in rows)
        stopped_count = sum(row.stopped_out is True for row in rows)
        false_breakout_count = sum(row.false_breakout is True for row in rows)
        positive_20d_count = sum((row.forward_return_20d or 0) > 0 for row in rows)
        positive_60d_count = sum((row.forward_return_60d or 0) > 0 for row in rows)
        return ScannerOutcomeSummary(
            total=total,
            pending_count=pending_count,
            matured_count=matured_count,
            triggered_count=triggered_count,
            stopped_count=stopped_count,
            false_breakout_count=false_breakout_count,
            positive_20d_count=positive_20d_count,
            positive_60d_count=positive_60d_count,
            trigger_rate=_rate(triggered_count, total),
            stop_rate=_rate(stopped_count, triggered_count),
            false_breakout_rate=_rate(false_breakout_count, triggered_count),
            positive_20d_rate=_rate(
                positive_20d_count,
                sum(row.forward_return_20d is not None for row in rows),
            ),
            positive_60d_rate=_rate(
                positive_60d_count,
                sum(row.forward_return_60d is not None for row in rows),
            ),
            avg_forward_return_20d=_average(row.forward_return_20d for row in rows),
            avg_forward_return_60d=_average(row.forward_return_60d for row in rows),
            avg_mfe_20d=_average(row.mfe_20d for row in rows),
            avg_mfe_60d=_average(row.mfe_60d for row in rows),
            avg_mae_20d=_average(row.mae_20d for row in rows),
            avg_mae_60d=_average(row.mae_60d for row in rows),
        )

    @staticmethod
    def get_candidate_outcome(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> ScannerOutcome:
        outcome = session.scalar(
            select(db.ScannerOutcome).where(
                db.ScannerOutcome.account_id == principal.account_id,
                db.ScannerOutcome.candidate_id == candidate_id,
            )
        )
        if outcome is None:
            raise ValueError(f"Scanner outcome not found for candidate: {candidate_id}")
        return ScannerOutcome.model_validate(outcome)

    @classmethod
    def recalculate_scanner_outcomes(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: ScannerOutcomeRecalculateRequest,
    ) -> ScannerOutcomeRecalculateResponse:
        statement = cls._candidate_list_statement(principal=principal)
        if request.candidate_id:
            statement = statement.where(db.Candidate.candidate_id == request.candidate_id)
        if request.symbol:
            statement = statement.where(db.Candidate.symbol_id == request.symbol.strip().upper())
        if request.strategy_name:
            statement = statement.where(db.Candidate.strategy_name == request.strategy_name.strip())
        statement = statement.order_by(db.Candidate.scan_date.desc(), db.Candidate.created_at.desc())
        if request.limit is not None:
            statement = statement.limit(request.limit)

        candidates = list(session.scalars(statement).all())
        if request.candidate_id and not candidates:
            raise ValueError(f"Candidate not found: {request.candidate_id}")

        status_counts: Counter[str] = Counter()
        symbols: set[str] = set()
        for candidate in candidates:
            outcome = ScannerOutcomeService.calculate_for_candidate(session=session, candidate=candidate)
            status_counts[outcome.evaluation_status] += 1
            symbols.add(outcome.symbol_id)

        if candidates:
            cls._audit(
                session,
                principal,
                "candidate.outcome_recalculate",
                "scanner_outcome",
                request.candidate_id,
            )
        session.commit()
        return ScannerOutcomeRecalculateResponse(
            account_id=principal.account_id,
            candidates_scanned=len(candidates),
            outcomes_written=len(candidates),
            skipped_candidates=0,
            status_counts=dict(status_counts),
            symbols_processed=sorted(symbols),
        )

    @staticmethod
    def _scanner_outcome_statement(
        *,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
    ):
        statement = select(db.ScannerOutcome).where(db.ScannerOutcome.account_id == principal.account_id)
        if evaluation_status:
            statement = statement.where(db.ScannerOutcome.evaluation_status == evaluation_status)
        if symbol:
            statement = statement.where(db.ScannerOutcome.symbol_id == symbol.strip().upper())
        return statement

    @classmethod
    def _delete_account_oneil_candidates_and_outcomes(
        cls,
        session: Session,
        principal: AuthPrincipal,
    ) -> None:
        cls._delete_account_strategy_candidates_and_outcomes(
            session,
            principal,
            ONEIL_CORE_US_ETF_STRATEGY,
        )

    @staticmethod
    def _delete_account_strategy_candidates_and_outcomes(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str,
    ) -> None:
        candidate_ids = select(db.Candidate.candidate_id).where(
            db.Candidate.account_id == principal.account_id,
            db.Candidate.strategy_name == strategy_name,
        )
        session.execute(
            delete(db.ScannerOutcome).where(db.ScannerOutcome.candidate_id.in_(candidate_ids))
        )
        session.execute(
            delete(db.Candidate).where(
                db.Candidate.account_id == principal.account_id,
                db.Candidate.strategy_name == strategy_name,
            )
        )
