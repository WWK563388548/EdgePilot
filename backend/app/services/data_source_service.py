from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal, AuthService
from backend.app.core.config import settings
from backend.app.services.polygon_client import PolygonClient

POLYGON_US_ETF_DAILY_CAPABILITY = "market_data.us_etf_daily"


class DataSourceUnavailable(ValueError):
    def __init__(self, capability_key: str, status: str, reason: str | None) -> None:
        self.capability_key = capability_key
        self.status = status
        self.reason = reason
        detail = reason or f"{capability_key} is {status}"
        super().__init__(f"Data source unavailable: {capability_key} is {status}. {detail}")


@dataclass(frozen=True)
class DataSourceResolution:
    provider: str
    capability_key: str
    source: str
    api_key: str
    credential_id: str | None = None

    def metadata(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "capability_key": self.capability_key,
            "source": self.source,
            "credential_id": self.credential_id,
        }


@dataclass(frozen=True)
class DataSourceCheckResult:
    provider: str
    capability_key: str
    status: str
    source: str | None
    message: str | None
    checked_at: datetime
    credential_id: str | None = None


class DataSourceService:
    @staticmethod
    def polygon_client_for_tenant(
        session: Session,
        principal: AuthPrincipal,
    ) -> tuple[PolygonClient, DataSourceResolution]:
        AuthService.ensure_tenant_foundation(session=session, tenant_id=principal.tenant_id)
        session.flush()
        resolution = DataSourceService.resolve_polygon_market_data(session, principal.tenant_id)
        capability = session.scalar(
            select(db.TenantDataCapability).where(
                db.TenantDataCapability.tenant_id == principal.tenant_id,
                db.TenantDataCapability.capability_key == POLYGON_US_ETF_DAILY_CAPABILITY,
            )
        )
        if capability is None:
            raise DataSourceUnavailable(
                POLYGON_US_ETF_DAILY_CAPABILITY,
                "missing",
                "Polygon market data capability is not registered",
            )
        if resolution is None or capability.status != "available":
            raise DataSourceUnavailable(
                POLYGON_US_ETF_DAILY_CAPABILITY,
                capability.status,
                capability.reason,
            )
        return (
            PolygonClient(api_key=resolution.api_key, base_url=settings.polygon_base_url),
            resolution,
        )

    @staticmethod
    def resolve_polygon_market_data(
        session: Session,
        tenant_id: str,
    ) -> DataSourceResolution | None:
        if settings.polygon_api_key:
            return DataSourceResolution(
                provider="polygon",
                capability_key=POLYGON_US_ETF_DAILY_CAPABILITY,
                source="env",
                api_key=settings.polygon_api_key,
            )

        credential = DataSourceService._configured_polygon_credential(session, tenant_id)
        if credential and credential.encrypted_payload:
            return DataSourceResolution(
                provider="polygon",
                capability_key=POLYGON_US_ETF_DAILY_CAPABILITY,
                source="tenant_credential",
                api_key=credential.encrypted_payload,
                credential_id=credential.credential_id,
            )
        return None

    @staticmethod
    def sync_polygon_capability(
        session: Session,
        tenant_id: str,
        *,
        status: str | None = None,
        source: str | None = None,
        reason: str | None = None,
        checked_at: datetime | None = None,
    ) -> db.TenantDataCapability:
        AuthService.ensure_tenant_foundation(session=session, tenant_id=tenant_id)
        session.flush()
        capability = session.scalar(
            select(db.TenantDataCapability).where(
                db.TenantDataCapability.tenant_id == tenant_id,
                db.TenantDataCapability.capability_key == POLYGON_US_ETF_DAILY_CAPABILITY,
            )
        )
        if capability is None:
            raise DataSourceUnavailable(
                POLYGON_US_ETF_DAILY_CAPABILITY,
                "missing",
                "Polygon market data capability is not registered",
            )

        if status is None:
            resolution = DataSourceService.resolve_polygon_market_data(session, tenant_id)
            if resolution:
                status = "available"
                source = resolution.source
                reason = None
            else:
                status = "missing"
                source = "env_or_tenant_credential"
                reason = "POLYGON_API_KEY or tenant Polygon credential is not configured"

        capability.status = status
        capability.source = source
        capability.reason = reason
        if checked_at is not None:
            capability.last_checked_at = checked_at
        capability.updated_at = datetime.now(UTC)
        return capability

    @staticmethod
    def record_polygon_refresh_result(
        session: Session,
        tenant_id: str,
        *,
        success_count: int,
        failure_count: int,
        error_summary: str | None,
    ) -> db.TenantDataCapability:
        checked_at = datetime.now(UTC)
        if success_count > 0:
            return DataSourceService.sync_polygon_capability(
                session,
                tenant_id,
                status="available",
                source=DataSourceService._current_polygon_source(session, tenant_id),
                reason=None,
                checked_at=checked_at,
            )
        if failure_count > 0:
            status = "invalid" if _looks_like_auth_error(error_summary) else "stale"
            return DataSourceService.sync_polygon_capability(
                session,
                tenant_id,
                status=status,
                source=DataSourceService._current_polygon_source(session, tenant_id),
                reason=error_summary or "Polygon returned no successful symbol results",
                checked_at=checked_at,
            )
        return DataSourceService.sync_polygon_capability(
            session,
            tenant_id,
            checked_at=checked_at,
        )

    @staticmethod
    def check_polygon_connection(
        session: Session,
        principal: AuthPrincipal,
        *,
        credential_id: str | None = None,
    ) -> DataSourceCheckResult:
        checked_at = datetime.now(UTC)
        resolution = DataSourceService._resolution_for_check(
            session,
            principal.tenant_id,
            credential_id=credential_id,
        )
        if resolution is None:
            capability = DataSourceService.sync_polygon_capability(
                session,
                principal.tenant_id,
                status="missing",
                source="env_or_tenant_credential",
                reason="POLYGON_API_KEY or tenant Polygon credential is not configured",
                checked_at=checked_at,
            )
            session.flush()
            return DataSourceCheckResult(
                provider="polygon",
                capability_key=POLYGON_US_ETF_DAILY_CAPABILITY,
                status=capability.status,
                source=capability.source,
                message=capability.reason,
                checked_at=checked_at,
            )

        client = PolygonClient(api_key=resolution.api_key, base_url=settings.polygon_base_url)
        try:
            to_date = date.today()
            from_date = to_date - timedelta(days=14)
            rows = client.list_daily_bars("SPY", from_date=from_date, to_date=to_date)
            if not rows:
                raise RuntimeError("Polygon returned no SPY bars during connection check")
        except Exception as exc:
            message = str(exc)
            auth_error = _looks_like_auth_error(message)
            DataSourceService._mark_credential_check(
                session,
                resolution.credential_id,
                status="invalid" if auth_error else None,
                checked_at=checked_at,
            )
            capability = DataSourceService.sync_polygon_capability(
                session,
                principal.tenant_id,
                status="invalid" if auth_error else "stale",
                source=resolution.source,
                reason=message,
                checked_at=checked_at,
            )
            session.flush()
            return DataSourceCheckResult(
                provider="polygon",
                capability_key=POLYGON_US_ETF_DAILY_CAPABILITY,
                status=capability.status,
                source=capability.source,
                message=message,
                checked_at=checked_at,
                credential_id=resolution.credential_id,
            )

        DataSourceService._mark_credential_check(
            session,
            resolution.credential_id,
            status="configured",
            checked_at=checked_at,
        )
        capability = DataSourceService.sync_polygon_capability(
            session,
            principal.tenant_id,
            status="available",
            source=resolution.source,
            reason=None,
            checked_at=checked_at,
        )
        session.flush()
        return DataSourceCheckResult(
            provider="polygon",
            capability_key=POLYGON_US_ETF_DAILY_CAPABILITY,
            status=capability.status,
            source=capability.source,
            message="Polygon connection check succeeded",
            checked_at=checked_at,
            credential_id=resolution.credential_id,
        )

    @staticmethod
    def fingerprint_secret(secret: str | None) -> str | None:
        if not secret:
            return None
        return sha256(secret.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _resolution_for_check(
        session: Session,
        tenant_id: str,
        *,
        credential_id: str | None,
    ) -> DataSourceResolution | None:
        if credential_id:
            credential = session.get(db.TenantApiKey, credential_id)
            if credential is None or credential.tenant_id != tenant_id:
                raise ValueError(f"Data credential not found: {credential_id}")
            if credential.provider != "polygon" or not credential.encrypted_payload:
                return None
            return DataSourceResolution(
                provider="polygon",
                capability_key=POLYGON_US_ETF_DAILY_CAPABILITY,
                source="tenant_credential",
                api_key=credential.encrypted_payload,
                credential_id=credential.credential_id,
            )
        return DataSourceService.resolve_polygon_market_data(session, tenant_id)

    @staticmethod
    def _configured_polygon_credential(
        session: Session,
        tenant_id: str,
    ) -> db.TenantApiKey | None:
        return session.scalar(
            select(db.TenantApiKey)
            .where(
                db.TenantApiKey.tenant_id == tenant_id,
                db.TenantApiKey.provider == "polygon",
                db.TenantApiKey.encrypted_payload.is_not(None),
                or_(
                    db.TenantApiKey.status.is_(None),
                    db.TenantApiKey.status.in_(("configured", "available")),
                ),
            )
            .order_by(db.TenantApiKey.updated_at.desc())
        )

    @staticmethod
    def _current_polygon_source(session: Session, tenant_id: str) -> str:
        resolution = DataSourceService.resolve_polygon_market_data(session, tenant_id)
        return resolution.source if resolution else "env_or_tenant_credential"

    @staticmethod
    def _mark_credential_check(
        session: Session,
        credential_id: str | None,
        *,
        status: str | None,
        checked_at: datetime,
    ) -> None:
        if credential_id is None:
            return
        credential = session.get(db.TenantApiKey, credential_id)
        if credential is None:
            return
        if status is not None:
            credential.status = status
        credential.last_verified_at = checked_at
        credential.updated_at = checked_at


def _looks_like_auth_error(message: str | None) -> bool:
    if not message:
        return False
    lowered = message.lower()
    return "401" in lowered or "403" in lowered or "unauthorized" in lowered or "forbidden" in lowered
