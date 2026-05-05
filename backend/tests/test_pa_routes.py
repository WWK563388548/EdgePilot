from datetime import UTC, datetime

from backend.app.api.routes.pa import (
    calculate_etf_daily_facts,
    count_pa_setups,
    get_pa_setup,
    explain_pa_setup,
    list_pa_calibration,
    list_pa_facts,
    list_pa_setups,
    list_pa_structures,
    run_us_etf_oneil_core_scanner,
)
from backend.app.schemas.business import Candidate
from backend.app.schemas.pa import (
    ETFOneilScannerRequest,
    ETFOneilScannerResponse,
    ETFUniverseFactsRequest,
    PACalibrationStat,
    PAFact,
    PAFactsCalculationResponse,
    PAStructure,
    PASetup,
    PAEvidenceBar,
    PAEvidenceLevel,
    PASetupEvidence,
    PASetupExplain,
    StratScanRequest,
    StratScanResponse,
    StratSignal,
)


def _fact() -> PAFact:
    return PAFact(
        fact_id="pafact_spy_1d_2026-04-30",
        symbol_id="SPY",
        timeframe="1d",
        ts=datetime(2026, 4, 30, tzinfo=UTC),
        facts={"close": 500.0},
    )


def _setup() -> PASetup:
    return PASetup(
        setup_id="pasetup_spy_1d_2026-04-30_breakout",
        symbol_id="SPY",
        timeframe="1d",
        detected_ts=datetime(2026, 4, 30, tzinfo=UTC),
        setup_type="breakout",
        validation_status="shadow_only",
    )


def _setup_explain() -> PASetupExplain:
    return PASetupExplain(
        setup_id="pasetup_spy_1d_2026-04-30_breakout",
        symbol_id="SPY",
        timeframe="1d",
        detected_ts=datetime(2026, 4, 30, tzinfo=UTC),
        setup_type="breakout",
        validation_status="shadow_only",
        summary="SPY is a breakout setup.",
        strengths=["Price is holding above the 20MA and 50MA."],
        watchouts=["This setup is shadow-only."],
        score_breakdown={"total": 82},
        evidence=PASetupEvidence(
            bars=[
                PAEvidenceBar(
                    ts=datetime(2026, 4, 30, tzinfo=UTC),
                    open=500,
                    high=510,
                    low=495,
                    close=508,
                    sma_20=490,
                )
            ],
            levels=[PAEvidenceLevel(key="trigger_price", value=510.51, source="entry_plan")],
            latest_facts={"close": 508},
        ),
    )


def _strat_signal() -> StratSignal:
    return StratSignal(
        signal_id="strat_spy_1d_2026-04-30",
        symbol_id="SPY",
        timeframe="1d",
        ts=datetime(2026, 4, 30, tzinfo=UTC),
        bar_type="2U",
        previous_bar_type="1",
        pattern="inside_breakout",
        direction="long",
        trigger_price=510,
        trigger_stop=495,
        timeframe_continuity={"1d": "bullish"},
        can_create_trade_alone=False,
    )


def test_pa_read_routes(monkeypatch) -> None:
    from backend.app.api.routes import pa as pa_route

    monkeypatch.setattr(pa_route.PAService, "list_facts", lambda **kwargs: [_fact()])
    monkeypatch.setattr(
        pa_route.PAService,
        "list_structures",
        lambda **kwargs: [
            PAStructure(
                structure_id="structure_1",
                symbol_id="SPY",
                timeframe="1d",
                ts=datetime(2026, 4, 30, tzinfo=UTC),
                structure_type="uptrend",
            )
        ],
    )
    monkeypatch.setattr(pa_route.PAService, "list_setups", lambda **kwargs: [_setup()])
    monkeypatch.setattr(pa_route.PAService, "count_setups", lambda **kwargs: 1)
    monkeypatch.setattr(pa_route.PAService, "get_setup", lambda **kwargs: _setup())
    monkeypatch.setattr(pa_route.PAService, "explain_setup", lambda **kwargs: _setup_explain())
    monkeypatch.setattr(
        pa_route.PAService,
        "list_calibration_stats",
        lambda **kwargs: [
            PACalibrationStat(stat_id="stat_1", setup_type="breakout", sample_size=10)
        ],
    )
    monkeypatch.setattr(pa_route.StratService, "list_signals", lambda **kwargs: [_strat_signal()])
    monkeypatch.setattr(pa_route.StratService, "latest_signal", lambda **kwargs: _strat_signal())

    assert list_pa_facts("SPY", session=None)[0].fact_id.startswith("pafact")
    assert list_pa_structures("SPY", session=None)[0].structure_type == "uptrend"
    assert list_pa_setups(session=None)[0].validation_status == "shadow_only"
    assert count_pa_setups(session=None).total == 1
    assert get_pa_setup("setup_1", session=None).setup_type == "breakout"
    assert explain_pa_setup("setup_1", session=None).evidence.levels[0].key == "trigger_price"
    assert list_pa_calibration(session=None)[0].sample_size == 10
    assert pa_route.list_strat_signals(session=None)[0].pattern == "inside_breakout"
    assert pa_route.latest_strat_signal("SPY", session=None).bar_type == "2U"


def test_pa_write_trigger_routes(monkeypatch) -> None:
    from backend.app.api.routes import pa as pa_route

    monkeypatch.setattr(
        pa_route.PAService,
        "calculate_etf_daily_facts",
        lambda request: PAFactsCalculationResponse(
            timeframe=request.timeframe,
            symbols_processed=request.symbols or ["SPY"],
            facts_written=1,
            skipped_symbols=[],
        ),
    )
    monkeypatch.setattr(
        pa_route.ETFScannerService,
        "run_us_etf_oneil_core",
        lambda request: ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=request.symbols or ["SPY"],
            facts_written=1,
            setups_written=1,
            candidates_written=1,
            candidates=[
                Candidate(
                    candidate_id="cand_1",
                    symbol_id="SPY",
                    scan_date=datetime(2026, 4, 30, tzinfo=UTC).date(),
                    strategy_name="oneil_core_us_etf",
                    decision="watch",
                )
            ],
        ),
    )
    monkeypatch.setattr(
        pa_route.StratService,
        "scan",
        lambda request: StratScanResponse(
            timeframe=request.timeframe,
            symbols_processed=request.symbols or ["SPY"],
            signals_written=1,
            skipped_symbols=[],
        ),
    )

    facts_response = calculate_etf_daily_facts(
        ETFUniverseFactsRequest(symbols=["spy"]),
        _admin=None,
    )
    scanner_response = run_us_etf_oneil_core_scanner(
        ETFOneilScannerRequest(symbols=["spy"], account_id="acct_local"),
        _admin=None,
    )
    strat_response = pa_route.scan_strat_signals(
        StratScanRequest(symbols=["spy"]),
        _admin=None,
    )

    assert facts_response.symbols_processed == ["SPY"]
    assert scanner_response.candidates_written == 1
    assert strat_response.signals_written == 1
