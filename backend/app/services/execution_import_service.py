from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
import csv
import io
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    ExecutionCSVImportRequest,
    ExecutionFill,
    ExecutionImport,
    ExecutionImportError,
    ExecutionImportResult,
)
from backend.app.services.audit_service import AuditService


@dataclass(frozen=True)
class NormalizedFillRow:
    row_number: int
    symbol_id: str
    side: str
    quantity: float
    price: float
    executed_at: datetime
    asset_type: str
    fees: float
    currency: str | None
    position_id: str | None
    broker_account_id: str | None
    broker_order_id: str | None
    broker_execution_id: str | None
    idempotency_key: str
    raw_row: dict[str, Any]


class ExecutionImportService:
    @staticmethod
    def import_csv(
        session: Session,
        principal: AuthPrincipal,
        request: ExecutionCSVImportRequest,
    ) -> ExecutionImportResult:
        import_record = db.ExecutionImport(
            import_id=f"exec_import_{uuid4().hex}",
            account_id=principal.account_id,
            broker=request.broker,
            source_filename=request.source_filename,
            status="failed",
            rows_total=0,
            rows_imported=0,
            rows_skipped=0,
            rows_failed=0,
            metadata_json={"errors": []},
        )
        session.add(import_record)
        session.flush([import_record])

        fills: list[db.ExecutionFill] = []
        errors: list[ExecutionImportError] = []
        skipped = 0
        seen_keys: set[str] = set()
        rows = ExecutionImportService._read_csv_rows(request.csv_text)
        import_record.rows_total = len(rows)

        if not rows:
            errors.append(
                ExecutionImportError(
                    row_number=0,
                    message="CSV has no data rows.",
                    raw_row={},
                )
            )

        for row_number, row in rows:
            try:
                normalized = ExecutionImportService._normalize_row(
                    principal=principal,
                    broker=request.broker,
                    row_number=row_number,
                    row=row,
                )
                if normalized.idempotency_key in seen_keys or ExecutionImportService._fill_exists(
                    session,
                    normalized.idempotency_key,
                ):
                    skipped += 1
                    seen_keys.add(normalized.idempotency_key)
                    continue
                try:
                    with session.begin_nested():
                        fill = ExecutionImportService._create_fill(
                            session=session,
                            principal=principal,
                            import_record=import_record,
                            normalized=normalized,
                        )
                        session.flush()
                except IntegrityError as exc:
                    if ExecutionImportService._is_duplicate_fill_conflict(exc):
                        skipped += 1
                        seen_keys.add(normalized.idempotency_key)
                        continue
                    raise
                fills.append(fill)
                seen_keys.add(normalized.idempotency_key)
            except ValueError as exc:
                errors.append(
                    ExecutionImportError(
                        row_number=row_number,
                        message=str(exc),
                        raw_row=dict(row),
                    )
                )

        imported = len(fills)
        failed = len(errors)
        import_record.rows_imported = imported
        import_record.rows_skipped = skipped
        import_record.rows_failed = failed
        import_record.error_message = "; ".join(error.message for error in errors[:3]) or None
        import_record.status = ExecutionImportService._import_status(
            imported=imported,
            skipped=skipped,
            failed=failed,
        )
        import_record.metadata_json = {
            "errors": [error.model_dump(mode="json") for error in errors],
        }
        import_record.updated_at = datetime.now(UTC)
        AuditService.record(
            session,
            principal,
            "execution_import.create",
            "execution_import",
            import_record.import_id,
        )
        session.commit()
        session.refresh(import_record)
        for fill in fills:
            session.refresh(fill)

        return ExecutionImportResult(
            import_record=ExecutionImport.model_validate(import_record),
            fills=[ExecutionFill.model_validate(fill) for fill in fills],
            errors=errors,
        )

    @staticmethod
    def list_imports(
        session: Session,
        principal: AuthPrincipal,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionImport]:
        statement = ExecutionImportService.imports_statement(principal=principal, status=status)
        statement = statement.order_by(db.ExecutionImport.created_at.desc()).limit(limit).offset(offset)
        return [ExecutionImport.model_validate(row) for row in session.scalars(statement).all()]

    @staticmethod
    def count_imports(
        session: Session,
        principal: AuthPrincipal,
        *,
        status: str | None = None,
    ) -> int:
        statement = ExecutionImportService.imports_statement(principal=principal, status=status)
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def imports_statement(*, principal: AuthPrincipal, status: str | None = None):
        statement = select(db.ExecutionImport).where(
            db.ExecutionImport.account_id == principal.account_id
        )
        if status:
            statement = statement.where(db.ExecutionImport.status == status)
        return statement

    @staticmethod
    def list_fills(
        session: Session,
        principal: AuthPrincipal,
        *,
        symbol_id: str | None = None,
        position_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionFill]:
        statement = ExecutionImportService.fills_statement(
            principal=principal,
            symbol_id=symbol_id,
            position_id=position_id,
        )
        statement = statement.order_by(db.ExecutionFill.executed_at.desc()).limit(limit).offset(offset)
        return [ExecutionFill.model_validate(row) for row in session.scalars(statement).all()]

    @staticmethod
    def count_fills(
        session: Session,
        principal: AuthPrincipal,
        *,
        symbol_id: str | None = None,
        position_id: str | None = None,
    ) -> int:
        statement = ExecutionImportService.fills_statement(
            principal=principal,
            symbol_id=symbol_id,
            position_id=position_id,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def fills_statement(
        *,
        principal: AuthPrincipal,
        symbol_id: str | None = None,
        position_id: str | None = None,
    ):
        statement = select(db.ExecutionFill).where(
            db.ExecutionFill.account_id == principal.account_id
        )
        if symbol_id:
            statement = statement.where(db.ExecutionFill.symbol_id == symbol_id.upper())
        if position_id:
            statement = statement.where(db.ExecutionFill.position_id == position_id)
        return statement

    @staticmethod
    def _read_csv_rows(csv_text: str) -> list[tuple[int, dict[str, str]]]:
        reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff").strip()))
        if not reader.fieldnames:
            return []
        fieldnames = [ExecutionImportService._normalize_csv_header(key) for key in reader.fieldnames]
        reader.fieldnames = fieldnames
        return [
            (
                index,
                {
                    ExecutionImportService._normalize_csv_header(key): value
                    for key, value in row.items()
                    if key and ExecutionImportService._normalize_csv_header(key)
                },
            )
            for index, row in enumerate(reader, start=2)
        ]

    @staticmethod
    def _normalize_csv_header(key: str) -> str:
        return key.replace("\ufeff", "").strip()

    @staticmethod
    def _normalize_row(
        *,
        principal: AuthPrincipal,
        broker: str,
        row_number: int,
        row: dict[str, str],
    ) -> NormalizedFillRow:
        normalized_row = {key.strip().lower(): (value or "").strip() for key, value in row.items()}
        symbol_id = ExecutionImportService._required_value(
            normalized_row,
            ("symbol", "ticker", "symbol_id"),
        ).upper()
        side = ExecutionImportService._normalize_side(
            ExecutionImportService._required_value(
                normalized_row,
                ("side", "action", "transaction_type"),
            )
        )
        quantity = ExecutionImportService._positive_float(
            ExecutionImportService._required_value(
                normalized_row,
                ("quantity", "qty", "shares"),
            ),
            "quantity",
        )
        price = ExecutionImportService._positive_float(
            ExecutionImportService._required_value(
                normalized_row,
                ("price", "fill_price", "execution_price"),
            ),
            "price",
        )
        executed_at = ExecutionImportService._parse_datetime(
            ExecutionImportService._required_value(
                normalized_row,
                ("executed_at", "execution_time", "timestamp", "time", "date"),
            )
        )
        fees = ExecutionImportService._float_value(
            ExecutionImportService._optional_value(
                normalized_row,
                ("fees", "fee", "commission", "commissions"),
            ),
            default=0.0,
        )
        broker_execution_id = ExecutionImportService._optional_value(
            normalized_row,
            ("execution_id", "broker_execution_id", "exec_id"),
        )
        broker_order_id = ExecutionImportService._optional_value(
            normalized_row,
            ("order_id", "broker_order_id"),
        )
        provided_key = ExecutionImportService._optional_value(
            normalized_row,
            ("idempotency_key", "import_key"),
        )
        idempotency_key = ExecutionImportService._idempotency_key(
            account_id=principal.account_id,
            broker=broker,
            symbol_id=symbol_id,
            side=side,
            quantity=quantity,
            price=price,
            executed_at=executed_at,
            broker_order_id=broker_order_id,
            broker_execution_id=broker_execution_id,
            provided_key=provided_key,
        )
        return NormalizedFillRow(
            row_number=row_number,
            symbol_id=symbol_id,
            side=side,
            quantity=quantity,
            price=price,
            executed_at=executed_at,
            asset_type=ExecutionImportService._optional_value(
                normalized_row,
                ("asset_type", "security_type"),
            )
            or "equity",
            fees=fees,
            currency=ExecutionImportService._optional_value(
                normalized_row,
                ("currency", "ccy"),
            ),
            position_id=ExecutionImportService._optional_value(
                normalized_row,
                ("position_id", "edgepilot_position_id"),
            ),
            broker_account_id=ExecutionImportService._optional_value(
                normalized_row,
                ("broker_account_id", "account"),
            ),
            broker_order_id=broker_order_id,
            broker_execution_id=broker_execution_id,
            idempotency_key=idempotency_key,
            raw_row=dict(row),
        )

    @staticmethod
    def _create_fill(
        *,
        session: Session,
        principal: AuthPrincipal,
        import_record: db.ExecutionImport,
        normalized: NormalizedFillRow,
    ) -> db.ExecutionFill:
        position = ExecutionImportService._resolve_position(session, principal, normalized)
        if position is None and normalized.position_id:
            raise ValueError(f"Position not found: {normalized.position_id}")
        if position is not None and (position.symbol_id or "").upper() != normalized.symbol_id:
            raise ValueError(
                "Position symbol mismatch: "
                f"{position.position_id} is {position.symbol_id}, row symbol is {normalized.symbol_id}"
            )
        if position is None:
            position = ExecutionImportService._create_review_needed_position(
                session,
                principal,
                normalized,
            )
        elif position.status in ("closed", "cancelled"):
            raise ValueError(f"Position is not active: {position.position_id}")
        else:
            ExecutionImportService._apply_fill_to_position(position, normalized)

        gross_amount = round(normalized.quantity * normalized.price, 6)
        net_amount = (
            round(gross_amount + normalized.fees, 6)
            if normalized.side == "buy"
            else round(gross_amount - normalized.fees, 6)
        )
        fill = db.ExecutionFill(
            fill_id=f"exec_fill_{sha1(normalized.idempotency_key.encode('utf-8')).hexdigest()[:24]}",
            import_id=import_record.import_id,
            account_id=principal.account_id,
            position_id=position.position_id,
            idempotency_key=normalized.idempotency_key,
            broker=import_record.broker,
            broker_account_id=normalized.broker_account_id,
            broker_order_id=normalized.broker_order_id,
            broker_execution_id=normalized.broker_execution_id,
            symbol_id=normalized.symbol_id,
            asset_type=normalized.asset_type,
            side=normalized.side,
            quantity=normalized.quantity,
            price=normalized.price,
            gross_amount=gross_amount,
            fees=normalized.fees,
            net_amount=net_amount,
            currency=normalized.currency,
            executed_at=normalized.executed_at,
            raw_row_json=normalized.raw_row,
        )
        session.add(fill)
        return fill

    @staticmethod
    def _resolve_position(
        session: Session,
        principal: AuthPrincipal,
        normalized: NormalizedFillRow,
    ) -> db.Position | None:
        if normalized.position_id:
            return session.scalar(
                select(db.Position).where(
                    db.Position.position_id == normalized.position_id,
                    db.Position.account_id == principal.account_id,
                )
            )
        matches = session.scalars(
            select(db.Position)
            .where(
                db.Position.account_id == principal.account_id,
                db.Position.symbol_id == normalized.symbol_id,
                db.Position.status.in_(("planned", "open", "reduce")),
            )
            .order_by(db.Position.updated_at.desc())
            .limit(2)
        ).all()
        if len(matches) == 1:
            return matches[0]
        return None

    @staticmethod
    def _create_review_needed_position(
        session: Session,
        principal: AuthPrincipal,
        normalized: NormalizedFillRow,
    ) -> db.Position:
        position = db.Position(
            position_id=f"exec_review_{sha1(normalized.idempotency_key.encode('utf-8')).hexdigest()[:24]}",
            account_id=principal.account_id,
            symbol_id=normalized.symbol_id,
            asset_type=normalized.asset_type,
            strategy_name="execution_import",
            entry_date=normalized.executed_at if normalized.side == "buy" else None,
            entry_price=normalized.price if normalized.side == "buy" else None,
            quantity=normalized.quantity,
            status="review_needed",
            current_r=0,
            realized_pnl=0,
            unrealized_pnl=0,
        )
        session.add(position)
        return position

    @staticmethod
    def _apply_fill_to_position(position: db.Position, normalized: NormalizedFillRow) -> None:
        if normalized.side == "buy":
            existing_quantity = 0.0 if position.status == "planned" else float(position.quantity or 0)
            existing_cost = existing_quantity * float(position.entry_price or normalized.price)
            new_quantity = round(existing_quantity + normalized.quantity, 6)
            position.entry_price = round(
                (existing_cost + normalized.quantity * normalized.price) / new_quantity,
                6,
            )
            position.entry_date = position.entry_date or normalized.executed_at
            position.quantity = new_quantity
            position.status = "open"
        else:
            if position.status == "planned":
                raise ValueError(f"Cannot apply sell fill to planned position: {position.position_id}")
            if position.entry_price is None or position.quantity is None:
                raise ValueError(f"Position is missing entry data: {position.position_id}")
            if normalized.quantity > position.quantity:
                raise ValueError(f"Sell quantity exceeds position quantity: {position.position_id}")
            realized = round(
                (normalized.price - position.entry_price) * normalized.quantity - normalized.fees,
                6,
            )
            remaining_quantity = round(position.quantity - normalized.quantity, 6)
            position.realized_pnl = round((position.realized_pnl or 0) + realized, 6)
            position.quantity = remaining_quantity
            position.status = "closed" if remaining_quantity == 0 else "reduce"
        position.updated_at = datetime.now(UTC)

    @staticmethod
    def _fill_exists(session: Session, idempotency_key: str) -> bool:
        return (
            session.scalar(
                select(db.ExecutionFill.fill_id).where(
                    db.ExecutionFill.idempotency_key == idempotency_key
                )
            )
            is not None
        )

    @staticmethod
    def _is_duplicate_fill_conflict(exc: IntegrityError) -> bool:
        orig = getattr(exc, "orig", None)
        diag = getattr(orig, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None)
        if constraint_name in {
            "execution_fills_pkey",
            "idx_execution_fills_idempotency",
            "positions_pkey",
        }:
            return True
        message = str(orig or exc).lower()
        return any(
            marker in message
            for marker in (
                "execution_fills.fill_id",
                "execution_fills.idempotency_key",
                "idx_execution_fills_idempotency",
                "positions.position_id",
            )
        )

    @staticmethod
    def _required_value(row: dict[str, str], keys: tuple[str, ...]) -> str:
        value = ExecutionImportService._optional_value(row, keys)
        if value is None:
            raise ValueError(f"Missing required field: {'/'.join(keys)}")
        return value

    @staticmethod
    def _optional_value(row: dict[str, str], keys: tuple[str, ...]) -> str | None:
        for key in keys:
            value = row.get(key)
            if value:
                return value
        return None

    @staticmethod
    def _normalize_side(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"buy", "b", "bot", "bought"}:
            return "buy"
        if normalized in {"sell", "s", "sold"}:
            return "sell"
        raise ValueError(f"Unsupported side: {value}")

    @staticmethod
    def _positive_float(value: str, field_name: str) -> float:
        parsed = ExecutionImportService._float_value(value)
        if parsed <= 0:
            raise ValueError(f"{field_name} must be greater than 0")
        return parsed

    @staticmethod
    def _float_value(value: str | None, default: float | None = None) -> float:
        if value is None or value == "":
            if default is not None:
                return default
            raise ValueError("Missing numeric value")
        try:
            return float(value.replace(",", ""))
        except ValueError as exc:
            raise ValueError(f"Invalid numeric value: {value}") from exc

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        raw = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(f"Invalid executed_at value: {value}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _idempotency_key(
        *,
        account_id: str,
        broker: str,
        symbol_id: str,
        side: str,
        quantity: float,
        price: float,
        executed_at: datetime,
        broker_order_id: str | None,
        broker_execution_id: str | None,
        provided_key: str | None,
    ) -> str:
        raw_key = (
            provided_key
            or broker_execution_id
            or "|".join(
                (
                    broker_order_id or "",
                    symbol_id,
                    side,
                    f"{quantity:.8f}",
                    f"{price:.8f}",
                    executed_at.isoformat(),
                )
            )
        )
        raw = "|".join((account_id, broker, raw_key))
        return f"exec_key_{sha1(raw.encode('utf-8')).hexdigest()[:32]}"

    @staticmethod
    def _import_status(*, imported: int, skipped: int, failed: int) -> str:
        if failed and imported == 0 and skipped == 0:
            return "failed"
        if failed:
            return "partial"
        return "completed"
