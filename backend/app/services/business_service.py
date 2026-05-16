from sqlalchemy.orm import Session

from backend.app.core.auth import AuthPrincipal
from backend.app.services.audit_service import AuditService
from backend.app.services.business.candidates import BusinessCandidatesMixin
from backend.app.services.business.dashboard import BusinessDashboardMixin
from backend.app.services.business.exit_alerts import BusinessExitAlertsMixin
from backend.app.services.business.journal import BusinessJournalMixin
from backend.app.services.business.jobs import BusinessJobsMixin
from backend.app.services.business.notifications import BusinessNotificationsMixin
from backend.app.services.business.paper_review import BusinessPaperReviewMixin
from backend.app.services.business.positions import BusinessPositionsMixin
from backend.app.services.business.risk import BusinessRiskMixin
from backend.app.services.business.scanners import BusinessScannersMixin


class BusinessService(
    BusinessNotificationsMixin,
    BusinessRiskMixin,
    BusinessPaperReviewMixin,
    BusinessJobsMixin,
    BusinessScannersMixin,
    BusinessCandidatesMixin,
    BusinessPositionsMixin,
    BusinessExitAlertsMixin,
    BusinessJournalMixin,
    BusinessDashboardMixin,
):
    @staticmethod
    def _audit(
        session: Session,
        principal: AuthPrincipal,
        action: str,
        entity_type: str,
        entity_id: str | None,
    ) -> None:
        AuditService.record(session, principal, action, entity_type, entity_id)
