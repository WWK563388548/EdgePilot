from collections import Counter

from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.database import SessionLocal
from backend.app.schemas.business import Candidate
from backend.app.schemas.pa import (
    ETFRotationScannerRequest,
    ETFOneilScannerRequest,
    ETFOneilScannerResponse,
    PAFactsCalculationResponse,
)
from backend.app.services.pa_service import PAService
from backend.app.services.scanner_outcome_service import ScannerOutcomeService
from backend.app.services.scanners.common import ScoredETFSetup
from backend.app.services.scanners.oneil import _score_oneil_core_setup
from backend.app.services.scanners.persistence import _upsert_candidate, _upsert_pa_setup
from backend.app.services.scanners.queries import (
    _latest_facts,
    _latest_strat_plans,
    _latest_strat_signals,
    _market_context_score,
    _normalize_symbols,
    _one_month_return_zscores,
    _percentile_ranks,
)
from backend.app.services.scanners.rotation import _score_etf_rotation_setup
from backend.app.services.strat_service import StratService
from backend.app.services.universes import default_symbols_when_omitted

class ETFScannerService:
    @staticmethod
    def run_us_etf_oneil_core(request: ETFOneilScannerRequest) -> ETFOneilScannerResponse:
        with SessionLocal() as session:
            response = ETFScannerService.run_us_etf_oneil_core_for_session(session, request)
            session.commit()
            return response

    @staticmethod
    def run_us_etf_oneil_core_for_session(
        session: Session,
        request: ETFOneilScannerRequest,
    ) -> ETFOneilScannerResponse:
        if session.get(db.Account, request.account_id) is None:
            raise ValueError(f"Account not found: {request.account_id}")

        symbols = _normalize_symbols(default_symbols_when_omitted(request.symbols))
        if request.recalculate_facts:
            facts_result = PAService.calculate_and_store_daily_facts(
                session=session,
                symbols=symbols,
                timeframe=request.timeframe,
            )
        else:
            facts_result = PAFactsCalculationResponse(
                timeframe=request.timeframe,
                symbols_processed=symbols,
                facts_written=0,
            )
        StratService.calculate_and_store_signals(
            session=session,
            symbols=symbols,
            timeframe=request.timeframe,
        )
        latest_facts = _latest_facts(session, symbols, request.timeframe)
        latest_strat_signals = _latest_strat_signals(session, symbols, request.timeframe)
        latest_strat_plans = _latest_strat_plans(
            session=session,
            latest_facts=latest_facts,
            timeframe=request.timeframe,
        )
        ranks_3m = _percentile_ranks(latest_facts, "return_3m")
        ranks_6m = _percentile_ranks(latest_facts, "return_6m")
        market_score, market_context = _market_context_score(session)

        scored_setups: list[ScoredETFSetup] = []
        skipped_symbols = list(facts_result.skipped_symbols)
        for symbol in symbols:
            fact = latest_facts.get(symbol)
            if fact is None:
                if symbol not in skipped_symbols:
                    skipped_symbols.append(symbol)
                continue
            scored = _score_oneil_core_setup(
                fact=fact,
                rank_3m=ranks_3m.get(symbol, 0),
                rank_6m=ranks_6m.get(symbol, 0),
                market_score=market_score,
                market_context=market_context,
                strat_signal=latest_strat_signals.get(symbol),
                strat_plan=latest_strat_plans.get(symbol),
            )
            if scored and scored.total_score >= request.min_score:
                scored_setups.append(scored)

        scored_setups.sort(key=lambda item: item.total_score, reverse=True)
        selected_setups = scored_setups[: request.max_candidates]

        candidates: list[Candidate] = []
        for scored in selected_setups:
            setup = _upsert_pa_setup(session, scored)
            session.flush()
            candidate = _upsert_candidate(
                session=session,
                account_id=request.account_id,
                scored=scored,
                setup_id=setup.setup_id,
            )
            ScannerOutcomeService.calculate_for_candidate(session=session, candidate=candidate)
            candidate_schema = Candidate.model_validate(candidate)
            candidate_schema.pa_setup_grade = setup.setup_grade
            candidate_schema.validation_status = setup.validation_status
            candidates.append(candidate_schema)

        decision_counts = Counter(candidate.decision or "unknown" for candidate in candidates)
        latest_scan_date = max((candidate.scan_date for candidate in candidates), default=None)
        latest_bar_date = max((fact.ts.date() for fact in latest_facts.values()), default=None)

        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=sorted(latest_facts),
            facts_written=facts_result.facts_written,
            setups_written=len(selected_setups),
            candidates_written=len(candidates),
            decision_counts=dict(decision_counts),
            latest_scan_date=latest_scan_date,
            latest_bar_date=latest_bar_date,
            skipped_symbols=skipped_symbols,
            candidates=candidates,
        )

    @staticmethod
    def run_us_etf_rotation(
        request: ETFRotationScannerRequest,
    ) -> ETFOneilScannerResponse:
        with SessionLocal() as session:
            response = ETFScannerService.run_us_etf_rotation_for_session(session, request)
            session.commit()
            return response

    @staticmethod
    def run_us_etf_rotation_for_session(
        session: Session,
        request: ETFRotationScannerRequest,
    ) -> ETFOneilScannerResponse:
        if session.get(db.Account, request.account_id) is None:
            raise ValueError(f"Account not found: {request.account_id}")

        symbols = _normalize_symbols(default_symbols_when_omitted(request.symbols))
        if not symbols:
            return ETFOneilScannerResponse(
                account_id=request.account_id,
                timeframe=request.timeframe,
                symbols_scanned=[],
                facts_written=0,
                setups_written=0,
                candidates_written=0,
                decision_counts={},
                latest_scan_date=None,
                latest_bar_date=None,
                skipped_symbols=[],
                candidates=[],
            )

        facts_symbols = _normalize_symbols([*symbols, request.benchmark_symbol])
        if request.recalculate_facts:
            facts_result = PAService.calculate_and_store_daily_facts(
                session=session,
                symbols=facts_symbols,
                timeframe=request.timeframe,
            )
        else:
            facts_result = PAFactsCalculationResponse(
                timeframe=request.timeframe,
                symbols_processed=facts_symbols,
                facts_written=0,
            )
        StratService.calculate_and_store_signals(
            session=session,
            symbols=symbols,
            timeframe=request.timeframe,
        )
        latest_facts = _latest_facts(session, facts_symbols, request.timeframe)
        scan_facts = {symbol: fact for symbol, fact in latest_facts.items() if symbol in set(symbols)}
        latest_strat_signals = _latest_strat_signals(session, symbols, request.timeframe)
        latest_strat_plans = _latest_strat_plans(
            session=session,
            latest_facts=scan_facts,
            timeframe=request.timeframe,
        )
        ranks_3m = _percentile_ranks(scan_facts, "return_3m")
        ranks_6m = _percentile_ranks(scan_facts, "return_6m")
        ranks_12m = _percentile_ranks(scan_facts, "return_12m")
        one_month_zscores = _one_month_return_zscores(
            session=session,
            symbols=symbols,
            timeframe=request.timeframe,
            latest_facts=scan_facts,
        )
        market_score, market_context = _market_context_score(session)
        benchmark_fact = latest_facts.get(request.benchmark_symbol)

        scored_setups: list[ScoredETFSetup] = []
        skipped_symbols = [symbol for symbol in facts_result.skipped_symbols if symbol in symbols]
        for symbol in symbols:
            fact = scan_facts.get(symbol)
            if fact is None:
                if symbol not in skipped_symbols:
                    skipped_symbols.append(symbol)
                continue
            scored = _score_etf_rotation_setup(
                fact=fact,
                rank_3m=ranks_3m.get(symbol, 0),
                rank_6m=ranks_6m.get(symbol, 0),
                rank_12m=ranks_12m.get(symbol, 0),
                one_month_zscore=one_month_zscores.get(symbol),
                benchmark_fact=benchmark_fact,
                benchmark_symbol=request.benchmark_symbol,
                market_score=market_score,
                market_context=market_context,
                strat_signal=latest_strat_signals.get(symbol),
                strat_plan=latest_strat_plans.get(symbol),
            )
            if scored and scored.total_score >= request.min_score:
                scored_setups.append(scored)

        scored_setups.sort(key=lambda item: item.total_score, reverse=True)
        selected_setups = scored_setups[: request.max_candidates]

        candidates: list[Candidate] = []
        for scored in selected_setups:
            setup = _upsert_pa_setup(session, scored)
            session.flush()
            candidate = _upsert_candidate(
                session=session,
                account_id=request.account_id,
                scored=scored,
                setup_id=setup.setup_id,
            )
            ScannerOutcomeService.calculate_for_candidate(session=session, candidate=candidate)
            candidate_schema = Candidate.model_validate(candidate)
            candidate_schema.pa_setup_grade = setup.setup_grade
            candidate_schema.validation_status = setup.validation_status
            candidates.append(candidate_schema)

        decision_counts = Counter(candidate.decision or "unknown" for candidate in candidates)
        latest_scan_date = max((candidate.scan_date for candidate in candidates), default=None)
        latest_bar_date = max((fact.ts.date() for fact in scan_facts.values()), default=None)

        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=sorted(scan_facts),
            facts_written=facts_result.facts_written,
            setups_written=len(selected_setups),
            candidates_written=len(candidates),
            decision_counts=dict(decision_counts),
            latest_scan_date=latest_scan_date,
            latest_bar_date=latest_bar_date,
            skipped_symbols=skipped_symbols,
            candidates=candidates,
        )
