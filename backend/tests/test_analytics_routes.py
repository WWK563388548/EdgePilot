from datetime import date

import pytest
from fastapi import HTTPException

from backend.app.api.routes import analytics as analytics_route
from backend.app.api.routes.analytics import get_overview
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.analytics import AnalyticsOverviewResponse


def _principal() -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_local",
        account_id="acct_local",
        tenant_id="tenant_local",
        role="owner",
        external_subject="local-dev",
        email_verified=True,
    )


def test_analytics_overview_route_is_account_scoped(monkeypatch) -> None:
    captured = {}

    def _fake_overview(session, principal, from_date, to_date):
        captured["account_id"] = principal.account_id
        captured["from_date"] = from_date
        captured["to_date"] = to_date
        return AnalyticsOverviewResponse(
            from_date=from_date,
            to_date=to_date,
            equity=10_100,
            total_pnl=100,
            realized_pnl=80,
            unrealized_pnl=20,
            win_rate=0.5,
            profit_factor=2,
            expectancy_r=0.25,
            average_r=0.25,
            max_drawdown_pct=-0.01,
            current_drawdown_pct=0,
            trades_count=4,
            open_risk_pct=0.005,
        )

    monkeypatch.setattr(analytics_route.AnalyticsService, "overview", _fake_overview)

    response = get_overview(
        session=None,
        principal=_principal(),
        from_date=date(2026, 5, 1),
        to_date=date(2026, 5, 11),
    )

    assert captured == {
        "account_id": "acct_local",
        "from_date": date(2026, 5, 1),
        "to_date": date(2026, 5, 11),
    }
    assert response.realized_pnl == 80


def test_analytics_overview_route_returns_client_error_for_invalid_range(monkeypatch) -> None:
    def _fake_overview(session, principal, from_date, to_date):
        raise ValueError("from date must be before or equal to to date")

    monkeypatch.setattr(analytics_route.AnalyticsService, "overview", _fake_overview)

    with pytest.raises(HTTPException) as exc_info:
        get_overview(
            session=None,
            principal=_principal(),
            from_date=date(2026, 5, 11),
            to_date=date(2026, 5, 1),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "from date must be before or equal to to date"
