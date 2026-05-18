from datetime import UTC, date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import pytest

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.services.analytics_service import AnalyticsService


def _principal(user_id: str = "user_a", account_id: str = "acct_a") -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id,
        account_id=account_id,
        tenant_id=f"tenant_{account_id}",
        role="owner",
        external_subject=user_id,
        email_verified=True,
    )


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-05-11 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        for user_id, account_id in (("user_a", "acct_a"), ("user_b", "acct_b")):
            db_session.add(db.User(user_id=user_id, external_subject=user_id))
            db_session.add(db.Account(account_id=account_id, name=account_id))
            db_session.add(
                db.AccountMembership(account_id=account_id, user_id=user_id, role="owner")
            )
        db_session.commit()
        yield db_session


def test_analytics_overview_uses_ledger_fills_journal_and_open_marks(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.Candidate(
            candidate_id="cand_spy",
            account_id=principal.account_id,
            symbol_id="SPY",
            scan_date=date(2026, 5, 1),
            strategy_name="etf_rotation_us_etf",
            entry_trigger=100,
            initial_stop=90,
            decision="candidate",
        )
    )
    session.add_all(
        [
            db.Position(
                position_id="plan_cand_spy",
                account_id=principal.account_id,
                symbol_id="SPY",
                asset_type="etf",
                strategy_name="etf_rotation_us_etf",
                entry_date=datetime(2026, 5, 1, tzinfo=UTC),
                entry_price=101,
                quantity=0,
                initial_stop=90,
                current_stop=95,
                status="closed",
                realized_pnl=21,
            ),
            db.Position(
                position_id="pos_open",
                account_id=principal.account_id,
                symbol_id="QQQ",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_date=datetime(2026, 5, 2, tzinfo=UTC),
                entry_price=50,
                quantity=4,
                initial_stop=45,
                current_stop=46,
                status="open",
                realized_pnl=0,
                unrealized_pnl=0,
            ),
            db.Position(
                position_id="pos_manual",
                account_id=principal.account_id,
                symbol_id="IWM",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_date=datetime(2026, 5, 3, tzinfo=UTC),
                entry_price=200,
                quantity=0,
                initial_stop=190,
                current_stop=190,
                status="closed",
                realized_pnl=-5,
            ),
            db.Position(
                position_id="pos_old_closed",
                account_id=principal.account_id,
                symbol_id="DIA",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_date=datetime(2026, 4, 1, tzinfo=UTC),
                entry_price=300,
                quantity=0,
                initial_stop=280,
                current_stop=280,
                status="closed",
                realized_pnl=100,
            ),
            db.Position(
                position_id="pos_other_account",
                account_id="acct_b",
                symbol_id="SMH",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_price=10,
                quantity=1,
                initial_stop=9,
                current_stop=9,
                status="open",
            ),
            db.Position(
                position_id="pos_future_open",
                account_id=principal.account_id,
                symbol_id="XLK",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_date=datetime(2026, 5, 20, tzinfo=UTC),
                entry_price=100,
                quantity=10,
                initial_stop=90,
                current_stop=90,
                status="open",
                realized_pnl=0,
                unrealized_pnl=999,
            ),
        ]
    )
    session.add(
        db.Bar(
            symbol_id="QQQ",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=55,
            source="test",
        )
    )
    session.add(
        db.ExecutionImport(
            import_id="exec_import_analytics",
            account_id=principal.account_id,
            broker="edgepilot_generic_csv",
            status="completed",
        )
    )
    session.add_all(
        [
            db.ExecutionFill(
                fill_id="exec_fill_buy",
                import_id="exec_import_analytics",
                account_id=principal.account_id,
                position_id="plan_cand_spy",
                idempotency_key="buy",
                broker="edgepilot_generic_csv",
                symbol_id="SPY",
                asset_type="etf",
                side="buy",
                quantity=2,
                price=101,
                fees=0,
                executed_at=datetime(2026, 5, 1, tzinfo=UTC),
                status="active",
                reconciliation_status="matched",
            ),
            db.ExecutionFill(
                fill_id="exec_fill_sell",
                import_id="exec_import_analytics",
                account_id=principal.account_id,
                position_id="plan_cand_spy",
                idempotency_key="sell",
                broker="edgepilot_generic_csv",
                symbol_id="SPY",
                asset_type="etf",
                side="sell",
                quantity=2,
                price=112,
                fees=1,
                executed_at=datetime(2026, 5, 10, tzinfo=UTC),
                status="active",
                reconciliation_status="matched",
            ),
        ]
    )
    session.add(
        db.TradeJournal(
            trade_id="trade_manual",
            account_id=principal.account_id,
            position_id="pos_manual",
            symbol_id="IWM",
            entry_ts=datetime(2026, 5, 3, tzinfo=UTC),
            exit_ts=datetime(2026, 5, 8, tzinfo=UTC),
            entry_price=200,
            exit_price=195,
            quantity=1,
            gross_pnl=-5,
            net_pnl=-5,
            r_multiple=-0.5,
            setup_type="oneil_core_us_etf",
        )
    )
    session.add(
        db.TradeJournal(
            trade_id="trade_old",
            account_id=principal.account_id,
            position_id="pos_old_closed",
            symbol_id="DIA",
            entry_ts=datetime(2026, 4, 1, tzinfo=UTC),
            exit_ts=datetime(2026, 4, 20, tzinfo=UTC),
            entry_price=300,
            exit_price=400,
            quantity=1,
            gross_pnl=100,
            net_pnl=100,
            r_multiple=5,
            setup_type="oneil_core_us_etf",
        )
    )
    session.commit()

    candidate_queries = []

    def _count_candidate_queries(conn, cursor, statement, parameters, context, executemany):
        if "from candidates" in statement.lower():
            candidate_queries.append(statement)

    event.listen(session.bind, "before_cursor_execute", _count_candidate_queries)
    overview = AnalyticsService.overview(
        session=session, principal=principal, from_date=date(2026, 5, 1), to_date=date(2026, 5, 11)
    )
    event.remove(session.bind, "before_cursor_execute", _count_candidate_queries)

    assert overview.realized_pnl == 16
    assert overview.unrealized_pnl == 20
    assert overview.total_pnl == 36
    assert overview.equity == 10136
    assert overview.trades_count == 2
    assert overview.win_rate == 0.5
    assert overview.profit_factor == 4.2
    assert overview.average_r == 0.25
    assert overview.open_positions_count == 1
    assert overview.closed_positions_count == 3
    assert overview.open_risk_pct == 0.001579
    assert [row.strategy_name for row in overview.strategy_breakdown] == [
        "etf_rotation_us_etf",
        "oneil_core_us_etf",
    ]
    assert overview.strategy_breakdown[0].realized_pnl == 21
    assert overview.strategy_breakdown[1].realized_pnl == -5
    assert overview.execution_quality.fills_count == 2
    assert overview.execution_quality.matched_fills_count == 2
    assert overview.execution_quality.planned_entry_count == 1
    assert overview.execution_quality.average_entry_drag_r == 0.1
    assert overview.execution_quality.average_entry_slippage_pct == 0.01
    assert overview.execution_quality.planned_exit_count == 1
    assert overview.execution_quality.average_exit_drag_r == -1.545455
    assert len(candidate_queries) == 1


def test_analytics_overview_preserves_historical_open_state_from_fills(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.Position(
            position_id="pos_closed_now",
            account_id=principal.account_id,
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="etf_rotation_us_etf",
            entry_date=datetime(2026, 5, 1, tzinfo=UTC),
            entry_price=100,
            quantity=0,
            initial_stop=90,
            current_stop=90,
            status="closed",
        )
    )
    session.add(
        db.Bar(
            symbol_id="SPY",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=110,
            source="test",
        )
    )
    session.add(
        db.ExecutionImport(
            import_id="exec_import_historical_open",
            account_id=principal.account_id,
            broker="edgepilot_generic_csv",
            status="completed",
        )
    )
    session.add_all(
        [
            db.ExecutionFill(
                fill_id="exec_fill_historical_buy",
                import_id="exec_import_historical_open",
                account_id=principal.account_id,
                position_id="pos_closed_now",
                idempotency_key="historical_buy",
                broker="edgepilot_generic_csv",
                symbol_id="SPY",
                asset_type="etf",
                side="buy",
                quantity=3,
                price=100,
                fees=0,
                executed_at=datetime(2026, 5, 1, tzinfo=UTC),
                status="active",
                reconciliation_status="matched",
            ),
            db.ExecutionFill(
                fill_id="exec_fill_historical_sell",
                import_id="exec_import_historical_open",
                account_id=principal.account_id,
                position_id="pos_closed_now",
                idempotency_key="historical_sell",
                broker="edgepilot_generic_csv",
                symbol_id="SPY",
                asset_type="etf",
                side="sell",
                quantity=3,
                price=120,
                fees=0,
                executed_at=datetime(2026, 5, 20, tzinfo=UTC),
                status="active",
                reconciliation_status="matched",
            ),
        ]
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.realized_pnl == 0
    assert overview.unrealized_pnl == 30
    assert overview.total_pnl == 30
    assert overview.equity == 10_030
    assert overview.open_positions_count == 1
    assert overview.closed_positions_count == 0
    assert overview.open_risk_pct == 0.002991


def test_analytics_overview_batches_mark_price_lookups(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add_all(
        [
            db.Position(
                position_id="pos_spy_open",
                account_id=principal.account_id,
                symbol_id="SPY",
                asset_type="etf",
                strategy_name="etf_rotation_us_etf",
                entry_date=datetime(2026, 5, 1, tzinfo=UTC),
                entry_price=100,
                quantity=2,
                initial_stop=90,
                current_stop=90,
                status="open",
            ),
            db.Position(
                position_id="pos_qqq_open",
                account_id=principal.account_id,
                symbol_id="QQQ",
                asset_type="etf",
                strategy_name="etf_rotation_us_etf",
                entry_date=datetime(2026, 5, 1, tzinfo=UTC),
                entry_price=200,
                quantity=1,
                initial_stop=180,
                current_stop=180,
                status="open",
            ),
            db.Position(
                position_id="pos_iwm_open",
                account_id=principal.account_id,
                symbol_id="IWM",
                asset_type="etf",
                strategy_name="etf_rotation_us_etf",
                entry_date=datetime(2026, 5, 1, tzinfo=UTC),
                entry_price=50,
                quantity=4,
                initial_stop=45,
                current_stop=45,
                status="open",
            ),
        ]
    )
    for bar in [
        db.Bar(
            symbol_id="SPY",
            timeframe="1d",
            ts=datetime(2026, 5, 9, tzinfo=UTC),
            close=101,
            source="test",
        ),
        db.Bar(
            symbol_id="SPY",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=110,
            source="test",
        ),
        db.Bar(
            symbol_id="QQQ",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=210,
            source="test",
        ),
        db.Bar(
            symbol_id="IWM",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=55,
            source="test",
        ),
    ]:
        session.add(bar)
        session.flush()
    session.commit()
    bar_queries = []

    def _count_bar_queries(conn, cursor, statement, parameters, context, executemany):
        if "from bars" in statement.lower() or "join bars" in statement.lower():
            bar_queries.append(statement)

    event.listen(session.bind, "before_cursor_execute", _count_bar_queries)
    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )
    event.remove(session.bind, "before_cursor_execute", _count_bar_queries)

    assert overview.unrealized_pnl == 50
    assert overview.open_positions_count == 3
    assert len(bar_queries) == 1


def test_analytics_overview_uses_journal_when_sell_fill_lacks_entry_price(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.Position(
            position_id="pos_sell_only",
            account_id=principal.account_id,
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="etf_rotation_us_etf",
            entry_date=datetime(2026, 5, 1, tzinfo=UTC),
            entry_price=None,
            quantity=0,
            initial_stop=None,
            current_stop=None,
            status="closed",
        )
    )
    session.add(
        db.ExecutionImport(
            import_id="exec_import_sell_only",
            account_id=principal.account_id,
            broker="edgepilot_generic_csv",
            status="completed",
        )
    )
    session.add(
        db.ExecutionFill(
            fill_id="exec_fill_sell_only",
            import_id="exec_import_sell_only",
            account_id=principal.account_id,
            position_id="pos_sell_only",
            idempotency_key="sell_only",
            broker="edgepilot_generic_csv",
            symbol_id="SPY",
            asset_type="etf",
            side="sell",
            quantity=2,
            price=120,
            fees=0,
            executed_at=datetime(2026, 5, 10, tzinfo=UTC),
            status="active",
            reconciliation_status="matched",
        )
    )
    session.add(
        db.TradeJournal(
            trade_id="trade_sell_only",
            account_id=principal.account_id,
            position_id="pos_sell_only",
            symbol_id="SPY",
            entry_ts=datetime(2026, 5, 1, tzinfo=UTC),
            exit_ts=datetime(2026, 5, 10, tzinfo=UTC),
            entry_price=100,
            exit_price=120,
            quantity=2,
            gross_pnl=40,
            net_pnl=39,
            r_multiple=2,
            setup_type="etf_rotation_us_etf",
        )
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.realized_pnl == 39
    assert overview.trades_count == 1
    assert overview.closed_positions_count == 1


def test_analytics_overview_aggregates_partial_sell_fills_as_one_trade(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.Position(
            position_id="pos_scaled_exit",
            account_id=principal.account_id,
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="etf_rotation_us_etf",
            entry_date=datetime(2026, 5, 1, tzinfo=UTC),
            entry_price=100,
            quantity=0,
            initial_stop=90,
            current_stop=90,
            status="closed",
        )
    )
    session.add(
        db.ExecutionImport(
            import_id="exec_import_scaled_exit",
            account_id=principal.account_id,
            broker="edgepilot_generic_csv",
            status="completed",
        )
    )
    session.add_all(
        [
            db.ExecutionFill(
                fill_id="exec_fill_scaled_sell_1",
                import_id="exec_import_scaled_exit",
                account_id=principal.account_id,
                position_id="pos_scaled_exit",
                idempotency_key="scaled_sell_1",
                broker="edgepilot_generic_csv",
                symbol_id="SPY",
                asset_type="etf",
                side="sell",
                quantity=1,
                price=110,
                fees=0,
                executed_at=datetime(2026, 5, 9, tzinfo=UTC),
                status="active",
                reconciliation_status="matched",
            ),
            db.ExecutionFill(
                fill_id="exec_fill_scaled_sell_2",
                import_id="exec_import_scaled_exit",
                account_id=principal.account_id,
                position_id="pos_scaled_exit",
                idempotency_key="scaled_sell_2",
                broker="edgepilot_generic_csv",
                symbol_id="SPY",
                asset_type="etf",
                side="sell",
                quantity=1,
                price=120,
                fees=2,
                executed_at=datetime(2026, 5, 10, tzinfo=UTC),
                status="active",
                reconciliation_status="matched",
            ),
        ]
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.realized_pnl == 28
    assert overview.trades_count == 1
    assert overview.win_rate == 1
    assert overview.average_r == 1.5
    assert overview.strategy_breakdown[0].trades_count == 1
    assert overview.strategy_breakdown[0].realized_pnl == 28
    assert overview.strategy_breakdown[0].average_r == 1.5


def test_analytics_overview_falls_back_to_default_equity_without_settings(session) -> None:
    principal = _principal()
    session.add(
        db.Position(
            position_id="pos_no_settings",
            account_id=principal.account_id,
            symbol_id="QQQ",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            entry_date=datetime(2026, 5, 1, tzinfo=UTC),
            entry_price=100,
            quantity=2,
            initial_stop=90,
            current_stop=90,
            status="open",
            unrealized_pnl=0,
        )
    )
    session.add(
        db.Bar(
            symbol_id="QQQ",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=105,
            source="test",
        )
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.unrealized_pnl == 10
    assert overview.equity == 10_010
    assert overview.open_risk_pct == 0.001998


def test_analytics_execution_quality_ignores_foreign_candidate(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.Candidate(
            candidate_id="cand_foreign",
            account_id="acct_b",
            symbol_id="SPY",
            scan_date=date(2026, 5, 1),
            strategy_name="etf_rotation_us_etf",
            entry_trigger=100,
            initial_stop=90,
            decision="candidate",
        )
    )
    session.add(
        db.Position(
            position_id="plan_cand_foreign",
            account_id=principal.account_id,
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="etf_rotation_us_etf",
            entry_date=datetime(2026, 5, 1, tzinfo=UTC),
            entry_price=101,
            quantity=1,
            initial_stop=90,
            current_stop=90,
            status="open",
        )
    )
    session.add(
        db.ExecutionImport(
            import_id="exec_import_foreign_candidate",
            account_id=principal.account_id,
            broker="edgepilot_generic_csv",
            status="completed",
        )
    )
    session.add(
        db.ExecutionFill(
            fill_id="exec_fill_foreign_candidate",
            import_id="exec_import_foreign_candidate",
            account_id=principal.account_id,
            position_id="plan_cand_foreign",
            idempotency_key="foreign_candidate",
            broker="edgepilot_generic_csv",
            symbol_id="SPY",
            asset_type="etf",
            side="buy",
            quantity=1,
            price=101,
            fees=0,
            executed_at=datetime(2026, 5, 1, tzinfo=UTC),
            status="active",
            reconciliation_status="matched",
        )
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.execution_quality.planned_entry_count == 0
    assert overview.execution_quality.average_entry_drag_r is None


def test_analytics_overview_rejects_reversed_date_range(session) -> None:
    with pytest.raises(ValueError):
        AnalyticsService.overview(
            session=session,
            principal=_principal(),
            from_date=date(2026, 5, 11),
            to_date=date(2026, 5, 1),
        )


def test_analytics_overview_prefers_latest_snapshot_equity(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.PortfolioSnapshot(
            account_id=principal.account_id,
            ts=datetime(2026, 5, 1, tzinfo=UTC),
            equity=10_500,
            cash=0,
            gross_exposure=0,
            net_exposure=0,
            open_risk_amount=0,
            open_risk_pct=0,
        )
    )
    session.flush()
    session.add(
        db.PortfolioSnapshot(
            account_id=principal.account_id,
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            equity=12_345,
            cash=0,
            gross_exposure=0,
            net_exposure=0,
            open_risk_amount=0,
            open_risk_pct=0,
        )
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.equity == 12_345


def test_analytics_overview_recomputes_equity_after_stale_snapshot(session) -> None:
    principal = _principal()
    session.add(
        db.AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=10_000,
            max_risk_per_trade_pct=0.005,
            max_total_risk_pct=0.02,
            max_open_positions=3,
        )
    )
    session.add(
        db.PortfolioSnapshot(
            account_id=principal.account_id,
            ts=datetime(2026, 5, 5, tzinfo=UTC),
            equity=10_050,
            cash=0,
            gross_exposure=0,
            net_exposure=0,
            open_risk_amount=0,
            open_risk_pct=0,
            realized_pnl=0,
            unrealized_pnl=10,
        )
    )
    session.add_all(
        [
            db.Position(
                position_id="pos_open_after_snapshot",
                account_id=principal.account_id,
                symbol_id="QQQ",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_date=datetime(2026, 5, 1, tzinfo=UTC),
                entry_price=100,
                quantity=1,
                initial_stop=90,
                current_stop=90,
                status="open",
            ),
            db.Position(
                position_id="pos_closed_after_snapshot",
                account_id=principal.account_id,
                symbol_id="SPY",
                asset_type="etf",
                strategy_name="etf_rotation_us_etf",
                entry_date=datetime(2026, 5, 1, tzinfo=UTC),
                entry_price=100,
                quantity=0,
                initial_stop=90,
                current_stop=90,
                status="closed",
            ),
        ]
    )
    session.add(
        db.Bar(
            symbol_id="QQQ",
            timeframe="1d",
            ts=datetime(2026, 5, 10, tzinfo=UTC),
            close=120,
            source="test",
        )
    )
    session.add(
        db.ExecutionImport(
            import_id="exec_import_stale_snapshot",
            account_id=principal.account_id,
            broker="edgepilot_generic_csv",
            status="completed",
        )
    )
    session.add(
        db.ExecutionFill(
            fill_id="exec_fill_sell_after_snapshot",
            import_id="exec_import_stale_snapshot",
            account_id=principal.account_id,
            position_id="pos_closed_after_snapshot",
            idempotency_key="sell_after_snapshot",
            broker="edgepilot_generic_csv",
            symbol_id="SPY",
            asset_type="etf",
            side="sell",
            quantity=1,
            price=115,
            fees=0,
            executed_at=datetime(2026, 5, 8, tzinfo=UTC),
            status="active",
            reconciliation_status="matched",
        )
    )
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.realized_pnl == 15
    assert overview.unrealized_pnl == 20
    assert overview.equity == 10_075
