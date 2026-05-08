from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import AccountRiskSettings, AccountRiskSettingsUpdate
from backend.app.services.audit_service import AuditService

DEFAULT_ACCOUNT_EQUITY = 10_000.0
DEFAULT_MAX_RISK_PER_TRADE_PCT = 0.005
DEFAULT_MAX_TOTAL_RISK_PCT = 0.02
DEFAULT_MAX_OPEN_POSITIONS = 3
DEFAULT_MAX_RISK_DISTANCE_PCT = 0.12


class RiskSettingsService:
    @staticmethod
    def get_account_risk_settings(
        session: Session,
        principal: AuthPrincipal,
    ) -> AccountRiskSettings:
        settings = RiskSettingsService.get_account_risk_settings_model(session, principal)
        return RiskSettingsService.risk_settings_response(principal, settings)

    @staticmethod
    def update_account_risk_settings(
        session: Session,
        principal: AuthPrincipal,
        request: AccountRiskSettingsUpdate,
    ) -> AccountRiskSettings:
        settings = RiskSettingsService.get_account_risk_settings_model(session, principal)
        if settings is None:
            settings = db.AccountRiskSettings(account_id=principal.account_id)
            session.add(settings)

        payload = request.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(settings, key, value)
        settings.updated_at = datetime.now(UTC)
        AuditService.record(session, principal, "risk_settings.update", "account", principal.account_id)
        session.commit()
        session.refresh(settings)
        return RiskSettingsService.risk_settings_response(principal, settings)

    @staticmethod
    def get_account_risk_settings_model(
        session: Session,
        principal: AuthPrincipal,
    ) -> db.AccountRiskSettings | None:
        return session.get(db.AccountRiskSettings, principal.account_id)

    @staticmethod
    def risk_settings_response(
        principal: AuthPrincipal,
        settings: db.AccountRiskSettings | None,
    ) -> AccountRiskSettings:
        return AccountRiskSettings(
            account_id=principal.account_id,
            account_equity=settings.account_equity if settings and settings.account_equity else DEFAULT_ACCOUNT_EQUITY,
            max_risk_per_trade_pct=(
                settings.max_risk_per_trade_pct
                if settings and settings.max_risk_per_trade_pct
                else DEFAULT_MAX_RISK_PER_TRADE_PCT
            ),
            max_total_risk_pct=(
                settings.max_total_risk_pct
                if settings and settings.max_total_risk_pct
                else DEFAULT_MAX_TOTAL_RISK_PCT
            ),
            max_open_positions=(
                settings.max_open_positions
                if settings and settings.max_open_positions
                else DEFAULT_MAX_OPEN_POSITIONS
            ),
            max_risk_distance_pct=(
                settings.max_risk_distance_pct
                if settings and settings.max_risk_distance_pct
                else DEFAULT_MAX_RISK_DISTANCE_PCT
            ),
            shadow_only_requires_paper=(
                settings.shadow_only_requires_paper
                if settings and settings.shadow_only_requires_paper is not None
                else True
            ),
            created_at=settings.created_at if settings else None,
            updated_at=settings.updated_at if settings else None,
        )
