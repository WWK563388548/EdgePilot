from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal, AuthService


class AuditService:
    @staticmethod
    def record(
        session: Session,
        principal: AuthPrincipal,
        action: str,
        entity_type: str,
        entity_id: str | None,
    ) -> None:
        session.add(
            db.AuditLog(
                audit_id=AuthService.audit_id(),
                account_id=principal.account_id,
                tenant_id=principal.tenant_id,
                actor_user_id=principal.user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )
