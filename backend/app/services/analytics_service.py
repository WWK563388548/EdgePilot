from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.analytics import (
    AnalyticsExecutionQuality,
    AnalyticsOverviewResponse,
    AnalyticsStrategyBreakdown,
)


ACTIVE_FILL_STATUSES = {"matched", "bound", "confirmed"}
ACTIVE_POSITION_STATUSES = {"open", "reduce"}


@dataclass(frozen=True)
class RealizedEvent:
    strategy_name: str
    pnl: float
    r_multiple: float | None


@dataclass(frozen=True)
class OpenPositionAsOf:
    position: db.Position
    quantity: float


class AnalyticsService:
    @staticmethod
    def overview(
        session: Session,
        principal: AuthPrincipal,
        from_date: date,
        to_date: date,
    ) -> AnalyticsOverviewResponse:
        if from_date > to_date:
            raise ValueError("from date must be before or equal to to date")

        from_ts = datetime.combine(from_date, time.min, tzinfo=UTC)
        to_ts = datetime.combine(to_date, time.max, tzinfo=UTC)
        positions = session.scalars(
            select(db.Position).where(db.Position.account_id == principal.account_id)
        ).all()
        positions_by_id = {position.position_id: position for position in positions}
        fills_until_to = session.scalars(
            select(db.ExecutionFill)
            .where(
                db.ExecutionFill.account_id == principal.account_id,
                db.ExecutionFill.executed_at <= to_ts,
                db.ExecutionFill.status == "active",
            )
            .order_by(db.ExecutionFill.executed_at.asc())
        ).all()
        fills = [
            fill
            for fill in fills_until_to
            if fill.executed_at is not None
            and AnalyticsService._as_utc(fill.executed_at) >= from_ts
        ]
        all_journals = session.scalars(
            select(db.TradeJournal).where(db.TradeJournal.account_id == principal.account_id)
        ).all()
        journals_until_to = [
            journal
            for journal in all_journals
            if journal.exit_ts and AnalyticsService._as_utc(journal.exit_ts) <= to_ts
        ]
        journals = [
            journal
            for journal in journals_until_to
            if journal.exit_ts and AnalyticsService._as_utc(journal.exit_ts) >= from_ts
        ]

        realized_events = AnalyticsService._realized_events(
            fills=fills,
            journals=journals,
            positions_by_id=positions_by_id,
        )
        realized_pnl = round(sum(event.pnl for event in realized_events), 6)
        open_positions = AnalyticsService._open_positions_as_of(
            positions=positions,
            fills_until_to=fills_until_to,
            all_journals=all_journals,
            to_ts=to_ts,
        )
        unrealized_pnl = AnalyticsService._unrealized_pnl(
            session=session,
            positions=open_positions,
            to_ts=to_ts,
        )
        total_pnl = round(realized_pnl + unrealized_pnl, 6)
        trades_count = len(realized_events)
        pnl_values = [event.pnl for event in realized_events]
        r_values = [event.r_multiple for event in realized_events if event.r_multiple is not None]
        wins = [value for value in pnl_values if value > 0]
        losses = [value for value in pnl_values if value < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        risk_settings = session.get(db.AccountRiskSettings, principal.account_id)
        equity = AnalyticsService._equity_as_of(
            session=session,
            principal=principal,
            positions_by_id=positions_by_id,
            risk_settings=risk_settings,
            to_ts=to_ts,
            journals_until_to=journals_until_to,
            fills_until_to=fills_until_to,
            unrealized_pnl=unrealized_pnl,
        )

        return AnalyticsOverviewResponse(
            from_date=from_date,
            to_date=to_date,
            equity=equity,
            total_pnl=total_pnl,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            win_rate=round(len(wins) / trades_count, 6) if trades_count else 0,
            profit_factor=round(gross_profit / gross_loss, 6) if gross_loss > 0 else 0,
            expectancy_r=round(mean(r_values), 6) if r_values else 0,
            average_r=round(mean(r_values), 6) if r_values else 0,
            max_drawdown_pct=AnalyticsService._max_drawdown_pct(
                session=session,
                principal=principal,
                from_ts=from_ts,
                to_ts=to_ts,
            ),
            current_drawdown_pct=AnalyticsService._current_drawdown_pct(
                session=session,
                principal=principal,
                to_ts=to_ts,
            ),
            trades_count=trades_count,
            open_risk_pct=AnalyticsService._open_risk_pct(open_positions, equity),
            open_positions_count=len(open_positions),
            closed_positions_count=AnalyticsService._closed_positions_count_as_of(
                positions=positions,
                open_positions=open_positions,
                fills_until_to=fills_until_to,
                all_journals=all_journals,
                to_ts=to_ts,
            ),
            strategy_breakdown=AnalyticsService._strategy_breakdown(realized_events),
            execution_quality=AnalyticsService._execution_quality(
                session=session,
                fills=fills,
                positions_by_id=positions_by_id,
            ),
        )

    @staticmethod
    def _realized_events(
        *,
        fills: list[db.ExecutionFill],
        journals: list[db.TradeJournal],
        positions_by_id: dict[str, db.Position],
    ) -> list[RealizedEvent]:
        events: list[RealizedEvent] = []
        sell_fill_position_ids: set[str] = set()
        for fill in fills:
            if fill.side != "sell" or fill.reconciliation_status == "ignored":
                continue
            position = positions_by_id.get(fill.position_id or "")
            if position is None:
                continue
            entry_price = position.entry_price
            if entry_price is None:
                continue
            pnl = round((fill.price - entry_price) * fill.quantity - (fill.fees or 0), 6)
            sell_fill_position_ids.add(position.position_id)
            events.append(
                RealizedEvent(
                    strategy_name=position.strategy_name or "unknown",
                    pnl=pnl,
                    r_multiple=AnalyticsService._r_multiple(
                        entry_price=entry_price,
                        stop=position.initial_stop or position.current_stop,
                        exit_price=fill.price,
                    ),
                )
            )

        for journal in journals:
            if journal.position_id in sell_fill_position_ids:
                continue
            pnl = journal.net_pnl if journal.net_pnl is not None else journal.gross_pnl
            if pnl is None:
                continue
            position = positions_by_id.get(journal.position_id or "")
            events.append(
                RealizedEvent(
                    strategy_name=journal.setup_type
                    or (position.strategy_name if position else None)
                    or "unknown",
                    pnl=round(pnl, 6),
                    r_multiple=journal.r_multiple,
                )
            )
        return events

    @staticmethod
    def _unrealized_pnl(
        *,
        session: Session,
        positions: list[OpenPositionAsOf],
        to_ts: datetime,
    ) -> float:
        total = 0.0
        for open_position in positions:
            position = open_position.position
            if position.entry_price is None:
                continue
            mark = AnalyticsService._latest_close(session, position.symbol_id, to_ts)
            if mark is None:
                if position.status in ACTIVE_POSITION_STATUSES:
                    total += float(position.unrealized_pnl or 0)
                continue
            total += (mark - position.entry_price) * open_position.quantity
        return round(total, 6)

    @staticmethod
    def _open_positions_as_of(
        *,
        positions: list[db.Position],
        fills_until_to: list[db.ExecutionFill],
        all_journals: list[db.TradeJournal],
        to_ts: datetime,
    ) -> list[OpenPositionAsOf]:
        fill_quantities = AnalyticsService._position_quantities_from_fills(fills_until_to)
        journal_quantities = AnalyticsService._position_quantities_from_journals(
            all_journals, to_ts
        )
        rows: list[OpenPositionAsOf] = []
        for position in positions:
            if AnalyticsService._position_start_ts(position) > to_ts:
                continue

            quantity = fill_quantities.get(position.position_id)
            if quantity is None:
                quantity = journal_quantities.get(position.position_id)
            if quantity is None and position.status in ACTIVE_POSITION_STATUSES:
                quantity = position.quantity
            if quantity is not None and quantity > 0:
                rows.append(OpenPositionAsOf(position=position, quantity=quantity))
        return rows

    @staticmethod
    def _position_quantities_from_fills(fills: list[db.ExecutionFill]) -> dict[str, float]:
        quantities: dict[str, float] = {}
        for fill in fills:
            if (
                not fill.position_id
                or fill.reconciliation_status == "ignored"
                or fill.quantity is None
            ):
                continue
            signed_quantity = fill.quantity if fill.side == "buy" else -fill.quantity
            quantities[fill.position_id] = quantities.get(fill.position_id, 0.0) + signed_quantity
        return quantities

    @staticmethod
    def _position_quantities_from_journals(
        journals: list[db.TradeJournal], to_ts: datetime
    ) -> dict[str, float]:
        quantities: dict[str, float] = {}
        for journal in journals:
            if not journal.position_id or journal.quantity is None:
                continue
            entry_ts = journal.entry_ts or datetime.min.replace(tzinfo=UTC)
            entry_ts = AnalyticsService._as_utc(entry_ts)
            exit_ts = journal.exit_ts
            if exit_ts is not None:
                exit_ts = AnalyticsService._as_utc(exit_ts)
            if entry_ts <= to_ts and (exit_ts is None or exit_ts > to_ts):
                quantities[journal.position_id] = (
                    quantities.get(journal.position_id, 0.0) + journal.quantity
                )
        return quantities

    @staticmethod
    def _closed_positions_count_as_of(
        *,
        positions: list[db.Position],
        open_positions: list[OpenPositionAsOf],
        fills_until_to: list[db.ExecutionFill],
        all_journals: list[db.TradeJournal],
        to_ts: datetime,
    ) -> int:
        open_position_ids = {row.position.position_id for row in open_positions}
        fill_quantities = AnalyticsService._position_quantities_from_fills(fills_until_to)
        position_ids_with_closing_fills = {
            fill.position_id
            for fill in fills_until_to
            if fill.position_id
            and fill.reconciliation_status != "ignored"
            and fill.quantity is not None
            and fill.side in {"buy", "sell"}
        }
        position_ids_with_journals = {
            journal.position_id for journal in all_journals if journal.position_id
        }
        position_ids_closed_by_journal = {
            journal.position_id
            for journal in all_journals
            if journal.position_id
            and journal.exit_ts is not None
            and AnalyticsService._as_utc(journal.exit_ts) <= to_ts
        }

        count = 0
        for position in positions:
            if position.position_id in open_position_ids:
                continue
            if AnalyticsService._position_start_ts(position) > to_ts:
                continue
            if position.position_id in position_ids_closed_by_journal:
                count += 1
                continue
            if (
                position.position_id in position_ids_with_closing_fills
                and fill_quantities.get(position.position_id, 0.0) <= 0
            ):
                count += 1
                continue
            if (
                position.status == "closed"
                and position.position_id not in fill_quantities
                and position.position_id not in position_ids_with_journals
                and AnalyticsService._position_close_fallback_ts(position) <= to_ts
            ):
                count += 1
        return count

    @staticmethod
    def _position_close_fallback_ts(position: db.Position) -> datetime:
        closed_at = position.updated_at or position.created_at or position.entry_date
        if closed_at is None:
            return datetime.max.replace(tzinfo=UTC)
        return AnalyticsService._as_utc(closed_at)

    @staticmethod
    def _position_start_ts(position: db.Position) -> datetime:
        started_at = position.entry_date or position.created_at or datetime.min.replace(tzinfo=UTC)
        return AnalyticsService._as_utc(started_at)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _latest_close(session: Session, symbol_id: str, to_ts: datetime) -> float | None:
        return session.scalar(
            select(db.Bar.close)
            .where(
                db.Bar.symbol_id == symbol_id,
                db.Bar.timeframe == "1d",
                db.Bar.ts <= to_ts,
                db.Bar.close.is_not(None),
            )
            .order_by(db.Bar.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _r_multiple(
        *,
        entry_price: float | None,
        stop: float | None,
        exit_price: float | None,
    ) -> float | None:
        if entry_price is None or stop is None or exit_price is None:
            return None
        risk = entry_price - stop
        if risk <= 0:
            return None
        return round((exit_price - entry_price) / risk, 6)

    @staticmethod
    def _open_risk_pct(positions: list[OpenPositionAsOf], equity: float) -> float:
        if equity <= 0:
            return 0
        risk_amount = 0.0
        for open_position in positions:
            position = open_position.position
            stop = position.current_stop or position.initial_stop
            if position.entry_price is None or stop is None:
                continue
            risk_per_unit = position.entry_price - stop
            if risk_per_unit > 0:
                risk_amount += risk_per_unit * open_position.quantity
        return round(risk_amount / equity, 6)

    @staticmethod
    def _equity_as_of(
        *,
        session: Session,
        principal: AuthPrincipal,
        positions_by_id: dict[str, db.Position],
        risk_settings: db.AccountRiskSettings | None,
        to_ts: datetime,
        journals_until_to: list[db.TradeJournal],
        fills_until_to: list[db.ExecutionFill],
        unrealized_pnl: float,
    ) -> float:
        snapshot_equity = AnalyticsService._latest_snapshot_equity(
            session=session,
            principal=principal,
            to_ts=to_ts,
        )
        if snapshot_equity is not None:
            return round(snapshot_equity, 6)

        account_equity = float(risk_settings.account_equity or 0) if risk_settings else 0.0
        realized_events = AnalyticsService._realized_events(
            fills=fills_until_to,
            journals=journals_until_to,
            positions_by_id=positions_by_id,
        )
        realized_pnl = sum(event.pnl for event in realized_events)
        return round(account_equity + realized_pnl + unrealized_pnl, 6)

    @staticmethod
    def _latest_snapshot_equity(
        *,
        session: Session,
        principal: AuthPrincipal,
        to_ts: datetime,
    ) -> float | None:
        return session.scalar(
            select(db.PortfolioSnapshot.equity)
            .where(
                db.PortfolioSnapshot.account_id == principal.account_id,
                db.PortfolioSnapshot.ts <= to_ts,
                db.PortfolioSnapshot.equity.is_not(None),
            )
            .order_by(db.PortfolioSnapshot.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _strategy_breakdown(events: list[RealizedEvent]) -> list[AnalyticsStrategyBreakdown]:
        grouped: dict[str, list[RealizedEvent]] = {}
        for event in events:
            grouped.setdefault(event.strategy_name, []).append(event)

        rows: list[AnalyticsStrategyBreakdown] = []
        for strategy_name, strategy_events in grouped.items():
            pnl_values = [event.pnl for event in strategy_events]
            r_values = [
                event.r_multiple for event in strategy_events if event.r_multiple is not None
            ]
            wins = [value for value in pnl_values if value > 0]
            losses = [value for value in pnl_values if value < 0]
            gross_loss = abs(sum(losses))
            rows.append(
                AnalyticsStrategyBreakdown(
                    strategy_name=strategy_name,
                    trades_count=len(strategy_events),
                    realized_pnl=round(sum(pnl_values), 6),
                    win_rate=round(len(wins) / len(strategy_events), 6)
                    if strategy_events
                    else None,
                    profit_factor=round(sum(wins) / gross_loss, 6) if gross_loss > 0 else None,
                    average_r=round(mean(r_values), 6) if r_values else None,
                )
            )
        return sorted(rows, key=lambda row: row.realized_pnl, reverse=True)

    @staticmethod
    def _execution_quality(
        *,
        session: Session,
        fills: list[db.ExecutionFill],
        positions_by_id: dict[str, db.Position],
    ) -> AnalyticsExecutionQuality:
        active_fills = [fill for fill in fills if fill.status == "active"]
        candidates_by_position_id = AnalyticsService._candidates_by_position_id(
            session=session,
            positions=positions_by_id.values(),
        )
        entry_drags: list[float] = []
        entry_slippage: list[float] = []
        exit_drags: list[float] = []
        for fill in active_fills:
            position = positions_by_id.get(fill.position_id or "")
            if position is None:
                continue
            candidate = candidates_by_position_id.get(position.position_id)
            planned_entry = candidate.entry_trigger if candidate else None
            planned_stop = (
                candidate.initial_stop
                if candidate and candidate.initial_stop is not None
                else position.initial_stop
            )
            risk = (
                planned_entry - planned_stop
                if planned_entry is not None and planned_stop is not None
                else None
            )
            if fill.side == "buy" and planned_entry is not None and planned_entry > 0:
                entry_slippage.append((fill.price - planned_entry) / planned_entry)
                if risk is not None and risk > 0:
                    entry_drags.append((fill.price - planned_entry) / risk)
            if fill.side == "sell":
                planned_exit = position.current_stop or position.initial_stop
                entry_price = position.entry_price
                stop = position.initial_stop or position.current_stop
                risk_for_exit = (
                    entry_price - stop if entry_price is not None and stop is not None else None
                )
                if planned_exit is not None and risk_for_exit is not None and risk_for_exit > 0:
                    exit_drags.append((planned_exit - fill.price) / risk_for_exit)

        return AnalyticsExecutionQuality(
            fills_count=len(active_fills),
            matched_fills_count=sum(
                1 for fill in active_fills if fill.reconciliation_status in ACTIVE_FILL_STATUSES
            ),
            review_needed_fills_count=sum(
                1 for fill in active_fills if fill.reconciliation_status == "review_needed"
            ),
            planned_entry_count=len(entry_slippage),
            average_entry_drag_r=round(mean(entry_drags), 6) if entry_drags else None,
            average_entry_slippage_pct=round(mean(entry_slippage), 6) if entry_slippage else None,
            planned_exit_count=len(exit_drags),
            average_exit_drag_r=round(mean(exit_drags), 6) if exit_drags else None,
        )

    @staticmethod
    def _candidates_by_position_id(
        *,
        session: Session,
        positions: Iterable[db.Position],
    ) -> dict[str, db.Candidate]:
        candidate_ids_by_position_id = {
            position.position_id: position.position_id.removeprefix("plan_")
            for position in positions
            if position.position_id.startswith("plan_")
            and position.position_id.removeprefix("plan_")
        }
        if not candidate_ids_by_position_id:
            return {}
        candidates = session.scalars(
            select(db.Candidate).where(
                db.Candidate.candidate_id.in_(candidate_ids_by_position_id.values()),
            )
        ).all()
        candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}
        return {
            position_id: candidates_by_id[candidate_id]
            for position_id, candidate_id in candidate_ids_by_position_id.items()
            if candidate_id in candidates_by_id
        }

    @staticmethod
    def _max_drawdown_pct(
        *,
        session: Session,
        principal: AuthPrincipal,
        from_ts: datetime,
        to_ts: datetime,
    ) -> float:
        snapshots = session.scalars(
            select(db.PortfolioSnapshot)
            .where(
                db.PortfolioSnapshot.account_id == principal.account_id,
                db.PortfolioSnapshot.ts >= from_ts,
                db.PortfolioSnapshot.ts <= to_ts,
            )
            .order_by(db.PortfolioSnapshot.ts.asc())
        ).all()
        peak: float | None = None
        max_drawdown = 0.0
        for snapshot in snapshots:
            equity = snapshot.equity
            if equity is None:
                continue
            peak = equity if peak is None else max(peak, equity)
            if peak > 0:
                max_drawdown = min(max_drawdown, (equity - peak) / peak)
        return round(max_drawdown, 6)

    @staticmethod
    def _current_drawdown_pct(
        *,
        session: Session,
        principal: AuthPrincipal,
        to_ts: datetime,
    ) -> float:
        snapshots = session.scalars(
            select(db.PortfolioSnapshot)
            .where(
                db.PortfolioSnapshot.account_id == principal.account_id,
                db.PortfolioSnapshot.ts <= to_ts,
            )
            .order_by(db.PortfolioSnapshot.ts.asc())
        ).all()
        if not snapshots:
            return 0
        equities = [snapshot.equity for snapshot in snapshots if snapshot.equity is not None]
        if not equities:
            return 0
        peak = max(equities)
        latest = equities[-1]
        return round((latest - peak) / peak, 6) if peak > 0 else 0
