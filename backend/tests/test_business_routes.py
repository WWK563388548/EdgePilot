from datetime import UTC, date, datetime

from backend.app.api.routes.business import (
    create_candidate,
    create_exit_alert,
    create_journal_trade,
    create_position,
    get_dashboard_summary,
    list_candidates,
    list_exit_alerts,
    list_journal_trades,
    list_positions,
    update_candidate,
    update_exit_alert,
    update_position,
)
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    Position,
    PositionCreate,
    PositionUpdate,
)


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="cand_1",
        symbol_id="SPY",
        scan_date=date(2026, 4, 26),
        strategy_name="breakout",
        decision="watch",
        created_at=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _position() -> Position:
    return Position(
        position_id="pos_1",
        symbol_id="SPY",
        asset_type="etf",
        status="open",
        quantity=10,
        created_at=datetime(2026, 4, 26, tzinfo=UTC),
        updated_at=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _alert() -> ExitAlert:
    return ExitAlert(
        alert_id="alert_1",
        position_id="pos_1",
        level=2,
        action="tighten_stop",
        acknowledged=False,
        alert_ts=datetime(2026, 4, 26, tzinfo=UTC),
    )


def _trade() -> JournalTrade:
    return JournalTrade(
        trade_id="trade_1",
        symbol_id="SPY",
        entry_ts=datetime(2026, 4, 20, tzinfo=UTC),
        exit_ts=datetime(2026, 4, 26, tzinfo=UTC),
        net_pnl=120.0,
    )


def test_candidate_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_candidate",
        lambda request: _candidate(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_candidates",
        lambda limit: [_candidate()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_candidate",
        lambda candidate_id, request: _candidate(),
    )

    assert create_candidate(
        CandidateCreate(
            symbol_id="SPY",
            scan_date=date(2026, 4, 26),
            strategy_name="breakout",
        )
    ).candidate_id == "cand_1"
    assert list_candidates(limit=10)[0].symbol_id == "SPY"
    assert update_candidate("cand_1", CandidateUpdate(decision="candidate")).decision == "watch"


def test_position_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_position",
        lambda request: _position(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_positions",
        lambda status, limit: [_position()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_position",
        lambda position_id, request: _position(),
    )

    assert create_position(PositionCreate(symbol_id="SPY", asset_type="etf")).position_id == "pos_1"
    assert list_positions(status_filter="open", limit=10)[0].status == "open"
    assert update_position("pos_1", PositionUpdate(current_stop=420)).symbol_id == "SPY"


def test_exit_alert_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_exit_alert",
        lambda request: _alert(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_exit_alerts",
        lambda acknowledged, limit: [_alert()],
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "update_exit_alert",
        lambda alert_id, request: _alert(),
    )

    assert create_exit_alert(ExitAlertCreate(position_id="pos_1")).alert_id == "alert_1"
    assert list_exit_alerts(acknowledged=False, limit=10)[0].level == 2
    assert update_exit_alert("alert_1", ExitAlertUpdate(acknowledged=True)).position_id == "pos_1"


def test_journal_routes(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "create_journal_trade",
        lambda request: _trade(),
    )
    monkeypatch.setattr(
        business_route.BusinessService,
        "list_journal_trades",
        lambda limit: [_trade()],
    )

    assert create_journal_trade(JournalTradeCreate(symbol_id="SPY")).trade_id == "trade_1"
    assert list_journal_trades(limit=10)[0].net_pnl == 120.0


def test_dashboard_summary_route(monkeypatch) -> None:
    from backend.app.api.routes import business as business_route

    monkeypatch.setattr(
        business_route.BusinessService,
        "dashboard_summary",
        lambda: DashboardSummary(
            market_context=MarketContextSummary(
                snapshot_ts=datetime(2026, 4, 26, tzinfo=UTC),
                risk_level="normal",
            ),
            risk_mode="normal",
            candidate_count=3,
            open_position_count=1,
            exit_alert_count=2,
            highest_exit_level=3,
            data_freshness=[
                DataFreshnessSummary(
                    dataset_key="bars:SPY:1d",
                    last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
                    source="polygon",
                )
            ],
        ),
    )

    response = get_dashboard_summary()

    assert response.risk_mode == "normal"
    assert response.candidate_count == 3
