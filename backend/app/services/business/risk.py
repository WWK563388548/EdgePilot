from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    AccountRiskSettings,
    AccountRiskSettingsUpdate,
    PortfolioRiskItem,
    PortfolioRiskSummary,
)
from backend.app.services.portfolio_risk_service import PortfolioRiskService
from backend.app.services.risk_settings_service import RiskSettingsService


class BusinessRiskMixin:
    @staticmethod
    def get_account_risk_settings(
        session: Session,
        principal: AuthPrincipal,
    ) -> AccountRiskSettings:
        return RiskSettingsService.get_account_risk_settings(session, principal)

    @staticmethod
    def update_account_risk_settings(
        session: Session,
        principal: AuthPrincipal,
        request: AccountRiskSettingsUpdate,
    ) -> AccountRiskSettings:
        return RiskSettingsService.update_account_risk_settings(session, principal, request)

    @staticmethod
    def get_portfolio_risk(
        session: Session,
        principal: AuthPrincipal,
    ) -> PortfolioRiskSummary:
        return PortfolioRiskService.get_portfolio_risk(session, principal)

    @staticmethod
    def _get_account_risk_settings_model(
        session: Session,
        principal: AuthPrincipal,
    ) -> db.AccountRiskSettings | None:
        return RiskSettingsService.get_account_risk_settings_model(session, principal)

    @staticmethod
    def _risk_settings_response(
        principal: AuthPrincipal,
        settings: db.AccountRiskSettings | None,
    ) -> AccountRiskSettings:
        return RiskSettingsService.risk_settings_response(principal, settings)

    @staticmethod
    def _portfolio_risk_summary(
        session: Session,
        principal: AuthPrincipal,
        *,
        extra_item: PortfolioRiskItem | None = None,
        exclude_position_id: str | None = None,
    ) -> PortfolioRiskSummary:
        return PortfolioRiskService.portfolio_risk_summary(
            session,
            principal,
            extra_item=extra_item,
            exclude_position_id=exclude_position_id,
        )

    @staticmethod
    def _portfolio_risk_item(
        position: db.Position,
        risk_settings: AccountRiskSettings,
    ) -> PortfolioRiskItem:
        return PortfolioRiskService.portfolio_risk_item(position, risk_settings)

    @staticmethod
    def _preview_portfolio_risk_item(
        *,
        candidate: db.Candidate,
        entry_price: float | None,
        initial_stop: float | None,
        quantity: float | None,
        risk_settings: AccountRiskSettings,
    ) -> PortfolioRiskItem:
        return PortfolioRiskService.preview_portfolio_risk_item(
            candidate=candidate,
            entry_price=entry_price,
            initial_stop=initial_stop,
            quantity=quantity,
            risk_settings=risk_settings,
        )
