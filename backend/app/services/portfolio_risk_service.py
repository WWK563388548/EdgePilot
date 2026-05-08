from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    AccountRiskSettings,
    GuardrailNotice,
    PortfolioRiskBucket,
    PortfolioRiskItem,
    PortfolioRiskSummary,
)
from backend.app.services.risk_settings_service import RiskSettingsService


def _candidate_plan_position_id(candidate_id: str) -> str:
    return f"plan_{candidate_id}"


def _risk_per_unit(entry_price: float | None, stop: float | None) -> float | None:
    if entry_price is None or stop is None:
        return None
    risk = entry_price - stop
    return round(risk, 6) if risk > 0 else None


def _risk_amount(entry_price: float | None, stop: float | None, quantity: float | None) -> float | None:
    risk = _risk_per_unit(entry_price, stop)
    if risk is None or quantity is None:
        return None
    return round(risk * quantity, 6)


class PortfolioRiskService:
    @staticmethod
    def get_portfolio_risk(
        session: Session,
        principal: AuthPrincipal,
    ) -> PortfolioRiskSummary:
        return PortfolioRiskService.portfolio_risk_summary(session, principal)

    @staticmethod
    def portfolio_risk_summary(
        session: Session,
        principal: AuthPrincipal,
        *,
        extra_item: PortfolioRiskItem | None = None,
        exclude_position_id: str | None = None,
    ) -> PortfolioRiskSummary:
        risk_settings = RiskSettingsService.get_account_risk_settings(session, principal)
        statement = (
            select(db.Position)
            .where(
                db.Position.account_id == principal.account_id,
                db.Position.status.in_(("planned", "open", "reduce")),
            )
            .order_by(db.Position.updated_at.desc())
        )
        rows = list(session.scalars(statement).all())
        items: list[PortfolioRiskItem] = []
        for row in rows:
            if exclude_position_id and row.position_id == exclude_position_id:
                continue
            items.append(PortfolioRiskService.portfolio_risk_item(row, risk_settings))
        if extra_item is not None:
            items.append(extra_item)

        total_risk_amount = round(
            sum(item.risk_amount or 0 for item in items),
            6,
        )
        total_risk_pct = round(total_risk_amount / risk_settings.account_equity, 6)
        max_total_risk_amount = round(
            risk_settings.account_equity * risk_settings.max_total_risk_pct,
            6,
        )
        remaining_risk_amount = round(max_total_risk_amount - total_risk_amount, 6)
        remaining_risk_pct = round(remaining_risk_amount / risk_settings.account_equity, 6)

        by_symbol: dict[str, dict[str, float | int]] = {}
        for item in items:
            bucket = by_symbol.setdefault(
                item.symbol_id,
                {"risk_amount": 0.0, "position_count": 0},
            )
            bucket["risk_amount"] = float(bucket["risk_amount"]) + (item.risk_amount or 0)
            bucket["position_count"] = int(bucket["position_count"]) + 1

        buckets = [
            PortfolioRiskBucket(
                symbol_id=symbol,
                risk_amount=round(float(bucket["risk_amount"]), 6),
                risk_pct=round(float(bucket["risk_amount"]) / risk_settings.account_equity, 6),
                position_count=int(bucket["position_count"]),
            )
            for symbol, bucket in by_symbol.items()
        ]
        buckets.sort(key=lambda bucket: bucket.risk_amount, reverse=True)

        notices: list[GuardrailNotice] = []
        if total_risk_pct > risk_settings.max_total_risk_pct:
            notices.append(GuardrailNotice(level="block", code="portfolio_risk_budget_exceeded"))
        elif remaining_risk_amount <= risk_settings.account_equity * risk_settings.max_risk_per_trade_pct:
            notices.append(GuardrailNotice(level="warning", code="portfolio_risk_budget_low"))
        if len(items) >= risk_settings.max_open_positions:
            notices.append(GuardrailNotice(level="warning", code="portfolio_position_limit_reached"))

        return PortfolioRiskSummary(
            account_id=principal.account_id,
            account_equity=risk_settings.account_equity,
            max_total_risk_pct=risk_settings.max_total_risk_pct,
            max_total_risk_amount=max_total_risk_amount,
            max_open_positions=risk_settings.max_open_positions,
            active_position_count=len(items),
            total_risk_amount=total_risk_amount,
            total_risk_pct=total_risk_pct,
            remaining_risk_amount=remaining_risk_amount,
            remaining_risk_pct=remaining_risk_pct,
            planned_risk_amount=round(
                sum(item.risk_amount or 0 for item in items if item.status == "planned"),
                6,
            ),
            open_risk_amount=round(
                sum(item.risk_amount or 0 for item in items if item.status == "open"),
                6,
            ),
            reduced_risk_amount=round(
                sum(item.risk_amount or 0 for item in items if item.status == "reduce"),
                6,
            ),
            highest_symbol_risk=buckets[0] if buckets else None,
            by_symbol=buckets,
            positions=items,
            notices=notices,
        )

    @staticmethod
    def portfolio_risk_item(
        position: db.Position,
        risk_settings: AccountRiskSettings,
    ) -> PortfolioRiskItem:
        stop = position.current_stop or position.initial_stop
        risk_amount = _risk_amount(position.entry_price, stop, position.quantity)
        return PortfolioRiskItem(
            position_id=position.position_id,
            symbol_id=position.symbol_id,
            status=position.status,
            entry_price=position.entry_price,
            stop_price=stop,
            quantity=position.quantity,
            risk_amount=risk_amount,
            risk_pct=(
                round(risk_amount / risk_settings.account_equity, 6)
                if risk_amount is not None
                else None
            ),
            source="position",
            updated_at=position.updated_at,
        )

    @staticmethod
    def preview_portfolio_risk_item(
        *,
        candidate: db.Candidate,
        entry_price: float | None,
        initial_stop: float | None,
        quantity: float | None,
        risk_settings: AccountRiskSettings,
    ) -> PortfolioRiskItem:
        risk_amount = _risk_amount(entry_price, initial_stop, quantity)
        return PortfolioRiskItem(
            position_id=_candidate_plan_position_id(candidate.candidate_id),
            symbol_id=candidate.symbol_id,
            status="planned",
            entry_price=entry_price,
            stop_price=initial_stop,
            quantity=quantity,
            risk_amount=risk_amount,
            risk_pct=(
                round(risk_amount / risk_settings.account_equity, 6)
                if risk_amount is not None
                else None
            ),
            source="preview",
        )
