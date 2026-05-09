import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.database import Base
from backend.app.schemas.pa import ETFRotationScannerRequest, ETFOneilScannerRequest
from backend.app.services.scanner_service import ETFScannerService
from backend.app.services.scanners.oneil import _scanner_decision
from backend.app.services.scanners.rotation import (
    _benchmark_relative_strength_score,
    _rotation_entry_mode,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-04-30 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        db_session.add(db.Account(account_id="acct_local", name="Local Dev"))
        _add_trending_bars(db_session, "SPY")
        db_session.commit()
        yield db_session


def test_us_etf_oneil_core_scanner_generates_pa_setup_and_candidate(session) -> None:
    response = ETFScannerService.run_us_etf_oneil_core_for_session(
        session,
        ETFOneilScannerRequest(symbols=["SPY"], account_id="acct_local", min_score=60),
    )
    session.commit()

    assert response.facts_written == 260
    assert response.setups_written == 1
    assert response.candidates_written == 1
    assert response.candidates[0].strategy_name == "oneil_core_us_etf"
    assert response.candidates[0].decision == "candidate"
    assert response.candidates[0].pa_setup_id is not None
    assert response.decision_counts == {"candidate": 1}
    assert response.latest_scan_date == response.candidates[0].scan_date
    assert response.latest_bar_date == response.candidates[0].scan_date

    setup = session.scalar(select(db.PASetup).where(db.PASetup.symbol_id == "SPY"))
    candidate = session.scalar(select(db.Candidate).where(db.Candidate.account_id == "acct_local"))
    outcome = session.scalar(select(db.ScannerOutcome).where(db.ScannerOutcome.account_id == "acct_local"))
    setup_count = session.scalar(
        select(func.count()).select_from(db.PASetup).where(db.PASetup.symbol_id == "SPY")
    )
    candidate_count = session.scalar(
        select(func.count()).select_from(db.Candidate).where(db.Candidate.account_id == "acct_local")
    )

    assert setup_count == 1
    assert candidate_count == 1
    assert setup is not None
    assert setup.entry_plan is not None
    scanner_decision = setup.entry_plan["scanner_decision"]
    assert scanner_decision["version"] == "oneil_core_us_etf_v2"
    assert scanner_decision["decision"] == "candidate"
    assert scanner_decision["strat_confirmation"]["status"] == "blocked"
    assert scanner_decision["strat_confirmation"]["can_create_trade_alone"] is False
    assert scanner_decision["score"] == scanner_decision["total_score"]
    assert scanner_decision["trigger_price"]
    assert scanner_decision["initial_stop"]
    assert scanner_decision["passed_rules"]
    passed_keys = {rule["key"] for rule in scanner_decision["passed_rules"]}
    failed_keys = {rule["key"] for rule in scanner_decision["failed_rules"]}
    assert "rs_top_quartile" in passed_keys
    assert "strat_consecutive_2u_no_chase" in failed_keys
    assert "breakout_close_near_high" in passed_keys
    assert "base_depth_healthy" in passed_keys
    assert "breakout_volume_missing" in failed_keys
    assert scanner_decision["metrics"]["rs_percentile_3m"] == 100
    assert scanner_decision["metrics"]["rs_percentile_6m"] == 100
    assert all(rule["passed"] for rule in scanner_decision["passed_rules"])
    assert candidate is not None
    assert candidate.ai_review_json is not None
    candidate_decision = json.loads(candidate.ai_review_json)["scanner_decision"]
    assert candidate_decision["score"] == scanner_decision["score"]
    assert candidate_decision["upgrade_conditions"]
    assert outcome is not None
    assert outcome.candidate_id == candidate.candidate_id
    assert outcome.evaluation_status == "pending"
    assert outcome.bars_available == 0


def test_us_etf_rotation_scanner_generates_separate_candidate(session) -> None:
    _add_compounding_bars(session, "QQQ")
    session.flush()
    response = ETFScannerService.run_us_etf_rotation_for_session(
        session,
        ETFRotationScannerRequest(symbols=["QQQ"], account_id="acct_local", min_score=60),
    )
    session.commit()

    assert response.facts_written == 520
    assert response.setups_written == 1
    assert response.candidates_written == 1
    assert response.candidates[0].strategy_name == "etf_rotation_us_etf"
    assert response.candidates[0].decision == "candidate"
    assert response.candidates[0].setup_type == "etf_rotation_leader"
    assert response.decision_counts == {"candidate": 1}

    setup = session.scalar(
        select(db.PASetup).where(db.PASetup.setup_type == "etf_rotation_leader")
    )
    candidate = session.scalar(
        select(db.Candidate).where(db.Candidate.strategy_name == "etf_rotation_us_etf")
    )

    assert setup is not None
    assert setup.entry_plan is not None
    assert setup.entry_plan["entry_mode"] == "breakout_allowed"
    assert setup.entry_plan["momentum_horizon"]["rank_3m"] == 100
    assert setup.entry_plan["momentum_horizon"]["rank_6m"] == 100
    assert setup.entry_plan["momentum_horizon"]["rank_12m"] == 100
    scanner_decision = setup.entry_plan["scanner_decision"]
    assert scanner_decision["version"] == "etf_rotation_us_etf_v1"
    assert scanner_decision["strategy"] == "etf_rotation_us_etf"
    assert scanner_decision["metrics"]["entry_mode"] == "breakout_allowed"
    assert scanner_decision["metrics"]["benchmark_relative_strength"]["benchmark_symbol"] == "SPY"
    assert candidate is not None
    assert json.loads(candidate.ai_review_json)["strategy_name"] == "etf_rotation_us_etf"


def test_us_etf_rotation_scanner_treats_explicit_empty_symbols_as_noop(session) -> None:
    response = ETFScannerService.run_us_etf_rotation_for_session(
        session,
        ETFRotationScannerRequest(symbols=[], account_id="acct_local", min_score=60),
    )

    assert response.symbols_scanned == []
    assert response.facts_written == 0
    assert response.setups_written == 0
    assert response.candidates_written == 0
    assert response.decision_counts == {}


def test_rotation_entry_mode_requires_pullback_when_one_month_is_extended() -> None:
    assert (
        _rotation_entry_mode(
            medium_term_strong=True,
            rank_3m=0.9,
            rank_6m=0.9,
            one_month_zscore=2.4,
        )
        == "pullback_required"
    )
    assert (
        _rotation_entry_mode(
            medium_term_strong=True,
            rank_3m=0.9,
            rank_6m=0.9,
            one_month_zscore=3.4,
        )
        == "watch_only"
    )
    assert (
        _rotation_entry_mode(
            medium_term_strong=True,
            rank_3m=0.9,
            rank_6m=0.9,
            one_month_zscore=-1.2,
        )
        == "retest_required"
    )


def test_benchmark_relative_strength_treats_equal_returns_as_neutral() -> None:
    facts = {
        "return_3m": 0.12,
        "return_6m": 0.2,
        "return_12m": 0.32,
    }

    score, metrics = _benchmark_relative_strength_score(
        facts=facts,
        benchmark_facts=facts,
        benchmark_symbol="SPY",
    )

    assert score == 5.0
    assert metrics["return_3m_vs_benchmark"] == 0
    assert metrics["return_6m_vs_benchmark"] == 0
    assert metrics["return_12m_vs_benchmark"] == 0


def test_scanner_decision_flags_bearish_strat_without_hiding_candidate() -> None:
    decision = _scanner_decision(
        base_score=12,
        base_depth=0.18,
        close_position=0.8,
        decision="candidate",
        distance_to_sma_20=0.03,
        initial_stop=95,
        market_score=8,
        quality_failed_rules=[],
        quality_passed_rules=["setup_location"],
        rank_3m=0.9,
        rank_6m=0.9,
        relative_volume=1.2,
        risk_stop_score=8,
        rs_score=22,
        setup_grade="A",
        setup_type="breakout",
        total_score=84,
        trend_score=24,
        trigger_price=105,
        volume_score=10,
        strat_signal=db.StratSignal(
            signal_id="strat_spy_1d_2026-04-30",
            symbol_id="SPY",
            timeframe="1d",
            ts=datetime(2026, 4, 30, tzinfo=UTC),
            bar_type="2D",
            previous_bar_type="1",
            pattern="inside_breakdown",
            direction="short",
            trigger_price=96,
            trigger_stop=104,
            can_create_trade_alone=False,
        ),
        strat_plan=None,
    )

    assert decision["decision"] == "candidate"
    assert decision["strat_confirmation"]["status"] == "downgrade"
    assert decision["strat_confirmation"]["base_decision"] == "candidate"
    assert decision["strat_confirmation"]["final_decision"] == "candidate"
    assert "strat_bearish_downgrade" in decision["watch_reasons"]
    assert any(rule["key"] == "strat_bearish_trigger" for rule in decision["failed_rules"])


def test_scanner_decision_surfaces_armed_strat_plan() -> None:
    decision = _scanner_decision(
        base_score=12,
        base_depth=0.18,
        close_position=0.8,
        decision="candidate",
        distance_to_sma_20=0.03,
        initial_stop=95,
        market_score=8,
        quality_failed_rules=[],
        quality_passed_rules=["setup_location"],
        rank_3m=0.9,
        rank_6m=0.9,
        relative_volume=1.2,
        risk_stop_score=8,
        rs_score=22,
        setup_grade="A",
        setup_type="breakout",
        total_score=84,
        trend_score=24,
        trigger_price=105,
        volume_score=10,
        strat_signal=None,
        strat_plan={
            "status": "armed",
            "latest_bar_type": "1",
            "pattern": "inside_breakout",
            "direction": "long",
            "trigger_price": 106.01,
            "trigger_stop": 101,
            "order_type": "buy_stop_limit",
            "stop_limit_price": 108.5,
            "max_entry_price": 108.5,
            "no_chase_rules": [{"level": "info", "code": "strat_gap_no_chase_limit"}],
        },
    )

    assert decision["decision"] == "candidate"
    assert decision["strat_confirmation"]["status"] == "armed"
    assert decision["strat_confirmation"]["trigger_price"] == 106.01
    assert decision["strat_confirmation"]["order_type"] == "buy_stop_limit"
    assert "strat_pending_trigger_armed" in decision["watch_reasons"]
    assert "strat_trigger_price_reached" in decision["upgrade_conditions"]


def test_scanner_decision_blocks_no_chase_strat_plan() -> None:
    decision = _scanner_decision(
        base_score=12,
        base_depth=0.18,
        close_position=0.8,
        decision="candidate",
        distance_to_sma_20=0.03,
        initial_stop=95,
        market_score=8,
        quality_failed_rules=[],
        quality_passed_rules=["setup_location"],
        rank_3m=0.9,
        rank_6m=0.9,
        relative_volume=1.2,
        risk_stop_score=8,
        rs_score=22,
        setup_grade="A",
        setup_type="breakout",
        total_score=84,
        trend_score=24,
        trigger_price=105,
        volume_score=10,
        strat_signal=None,
        strat_plan={
            "status": "blocked",
            "latest_bar_type": "2U",
            "pattern": "2U_continuation",
            "direction": "long",
            "trigger_price": 106.01,
            "trigger_stop": 90,
            "order_type": "buy_stop_limit",
            "no_chase_rules": [
                {"level": "block", "code": "strat_risk_too_wide"},
                {"level": "info", "code": "strat_gap_no_chase_limit"},
            ],
        },
    )

    assert decision["decision"] == "candidate"
    assert decision["strat_confirmation"]["status"] == "blocked"
    assert decision["strat_confirmation"]["final_decision"] == "candidate"
    assert "strat_no_chase_blocked" in decision["watch_reasons"]
    assert any(rule["key"] == "strat_risk_too_wide" for rule in decision["failed_rules"])


def test_us_etf_oneil_core_scanner_is_idempotent_for_same_scan_date(session) -> None:
    request = ETFOneilScannerRequest(symbols=["SPY"], account_id="acct_local", min_score=60)

    ETFScannerService.run_us_etf_oneil_core_for_session(session, request)
    ETFScannerService.run_us_etf_oneil_core_for_session(session, request)
    session.commit()

    candidate_count = session.scalar(
        select(func.count()).select_from(db.Candidate).where(db.Candidate.account_id == "acct_local")
    )

    assert candidate_count == 1


def test_us_etf_oneil_core_scanner_treats_explicit_empty_symbols_as_noop(session) -> None:
    response = ETFScannerService.run_us_etf_oneil_core_for_session(
        session,
        ETFOneilScannerRequest(symbols=[], account_id="acct_local", min_score=60),
    )

    assert response.symbols_scanned == []
    assert response.facts_written == 0
    assert response.setups_written == 0
    assert response.candidates_written == 0
    assert response.decision_counts == {}
    assert response.latest_scan_date is None
    assert response.latest_bar_date is None
    assert response.skipped_symbols == []

    candidate_count = session.scalar(
        select(func.count()).select_from(db.Candidate).where(db.Candidate.account_id == "acct_local")
    )
    assert candidate_count == 0


def _add_trending_bars(session, symbol: str) -> None:
    start = datetime(2025, 8, 13, tzinfo=UTC)
    for index in range(260):
        close = 100 + (index * 0.8)
        session.add(
            db.Bar(
                symbol_id=symbol,
                timeframe="1d",
                ts=start + timedelta(days=index),
                open=close - 1,
                high=close + 0.2,
                low=close - 2,
                close=close,
                volume=1_000_000 + (index * 2_000),
                adjusted=True,
                source="test",
            )
        )


def _add_compounding_bars(session, symbol: str) -> None:
    start = datetime(2025, 8, 13, tzinfo=UTC)
    for index in range(260):
        close = round(100 * (1.004**index), 4)
        session.add(
            db.Bar(
                symbol_id=symbol,
                timeframe="1d",
                ts=start + timedelta(days=index),
                open=close * 0.99,
                high=close * 1.003,
                low=close * 0.985,
                close=close,
                volume=1_500_000 + (index * 2_000),
                adjusted=True,
                source="test",
            )
        )
