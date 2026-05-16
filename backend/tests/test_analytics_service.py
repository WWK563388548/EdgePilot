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
    session.commit()

    overview = AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert overview.realized_pnl == 16
    assert overview.unrealized_pnl == 20
    assert overview.total_pnl == 36
    assert overview.equity == 10036
    assert overview.trades_count == 2
    assert overview.win_rate == 0.5
    assert overview.profit_factor == 4.2
    assert overview.average_r == 0.25
    assert overview.open_positions_count == 1
    assert overview.closed_positions_count == 2
    assert overview.open_risk_pct == 0.001594
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


def test_analytics_overview_rejects_reversed_date_range(session) -> None:
    with pytest.raises(ValueError):
        AnalyticsService.overview(
            session=session,
            principal=_principal(),
            from_date=date(2026, 5, 11),
            to_date=date(2026, 5, 1),
        )
