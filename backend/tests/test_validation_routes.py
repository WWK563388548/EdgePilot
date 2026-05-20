from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from backend.app.api.routes import validation as validation_route
from backend.app.api.routes.validation import (
    evaluate_strategy_readiness,
    list_strategy_readiness,
    update_strategy_kill_switch,
)
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.validation import (
    GoLiveGate,
    GoLiveGateEvaluateRequest,
    StrategyKillSwitch,
    StrategyKillSwitchUpdate,
    StrategyReadiness,
)


def _principal() -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_local",
        account_id="acct_local",
        tenant_id="tenant_local",
        role="owner",
        external_subject="local-dev",
        email_verified=True,
    )


def _gate(strategy_name: str = "etf_rotation_us_etf") -> GoLiveGate:
    return GoLiveGate(
        gate_id="gate_1",
        account_id="acct_local",
        strategy_name=strategy_name,
        stage="paper",
        status="paper_only",
        required_trades=30,
        current_trades=40,
        reasons=["needs_more_paper_evidence"],
        evaluated_at=datetime(2026, 5, 20, tzinfo=UTC),
    )


def test_validation_readiness_route_is_account_scoped(monkeypatch) -> None:
    captured = {}

    def _fake_list_readiness(session, principal):
        captured["account_id"] = principal.account_id
        return [StrategyReadiness(strategy_name="etf_rotation_us_etf", gate=_gate())]

    monkeypatch.setattr(validation_route.ValidationService, "list_readiness", _fake_list_readiness)

    response = list_strategy_readiness(session=None, principal=_principal())

    assert captured == {"account_id": "acct_local"}
    assert response[0].gate.status == "paper_only"


def test_validation_evaluate_route_maps_value_error_to_client_error(monkeypatch) -> None:
    def _fake_evaluate_strategy(session, principal, strategy_name, request):
        raise ValueError("strategy_name is required")

    monkeypatch.setattr(
        validation_route.ValidationService,
        "evaluate_strategy",
        _fake_evaluate_strategy,
    )

    with pytest.raises(HTTPException) as exc_info:
        evaluate_strategy_readiness(
            strategy_name=" ",
            request=GoLiveGateEvaluateRequest(),
            session=None,
            principal=_principal(),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "strategy_name is required"


def test_validation_kill_switch_route_delegates(monkeypatch) -> None:
    captured = {}

    def _fake_update_kill_switch(session, principal, strategy_name, request):
        captured["strategy_name"] = strategy_name
        captured["status"] = request.status
        return StrategyKillSwitch(
            account_id=principal.account_id,
            strategy_name=strategy_name,
            status=request.status,
            reason=request.reason,
        )

    monkeypatch.setattr(
        validation_route.ValidationService,
        "update_kill_switch",
        _fake_update_kill_switch,
    )

    response = update_strategy_kill_switch(
        strategy_name="etf_rotation_us_etf",
        request=StrategyKillSwitchUpdate(status="paused", reason="test"),
        session=None,
        principal=_principal(),
    )

    assert captured == {"strategy_name": "etf_rotation_us_etf", "status": "paused"}
    assert response.status == "paused"
