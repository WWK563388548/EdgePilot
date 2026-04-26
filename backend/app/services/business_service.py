from uuid import uuid4

from psycopg.rows import dict_row

from backend.app.core.database import connect
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    Position,
    PositionCreate,
    PositionUpdate,
)


class BusinessService:
    @staticmethod
    def create_candidate(request: CandidateCreate) -> Candidate:
        candidate_id = request.candidate_id or f"cand_{uuid4().hex}"
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO candidates (
                        candidate_id, symbol_id, scan_date, strategy_name, setup_type,
                        score_total, entry_trigger, initial_stop, decision,
                        option_suitability, ai_review_json
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        candidate_id,
                        request.symbol_id,
                        request.scan_date,
                        request.strategy_name,
                        request.setup_type,
                        request.score_total,
                        request.entry_trigger,
                        request.initial_stop,
                        request.decision,
                        request.option_suitability,
                        request.ai_review_json,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return Candidate(**row)

    @staticmethod
    def list_candidates(limit: int = 100) -> list[Candidate]:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM candidates
                    ORDER BY scan_date DESC, created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = list(cur.fetchall())
        return [Candidate(**row) for row in rows]

    @staticmethod
    def update_candidate(candidate_id: str, request: CandidateUpdate) -> Candidate:
        payload = request.model_dump(exclude_unset=True)
        if not payload:
            return BusinessService.get_candidate(candidate_id)

        assignments = ", ".join(f"{key} = %s" for key in payload)
        values = list(payload.values())
        values.append(candidate_id)
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"UPDATE candidates SET {assignments} WHERE candidate_id = %s RETURNING *",
                    values,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise ValueError(f"Candidate not found: {candidate_id}")
        return Candidate(**row)

    @staticmethod
    def get_candidate(candidate_id: str) -> Candidate:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT * FROM candidates WHERE candidate_id = %s", (candidate_id,))
                row = cur.fetchone()
        if row is None:
            raise ValueError(f"Candidate not found: {candidate_id}")
        return Candidate(**row)

    @staticmethod
    def create_position(request: PositionCreate) -> Position:
        position_id = request.position_id or f"pos_{uuid4().hex}"
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO positions (
                        position_id, symbol_id, asset_type, strategy_name, entry_date,
                        entry_price, quantity, initial_stop, current_stop, status,
                        current_r, realized_pnl, unrealized_pnl
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        position_id,
                        request.symbol_id,
                        request.asset_type,
                        request.strategy_name,
                        request.entry_date,
                        request.entry_price,
                        request.quantity,
                        request.initial_stop,
                        request.current_stop,
                        request.status,
                        request.current_r,
                        request.realized_pnl,
                        request.unrealized_pnl,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return Position(**row)

    @staticmethod
    def list_positions(status: str | None = None, limit: int = 100) -> list[Position]:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if status:
                    cur.execute(
                        """
                        SELECT *
                        FROM positions
                        WHERE status = %s
                        ORDER BY updated_at DESC
                        LIMIT %s
                        """,
                        (status, limit),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM positions ORDER BY updated_at DESC LIMIT %s",
                        (limit,),
                    )
                rows = list(cur.fetchall())
        return [Position(**row) for row in rows]

    @staticmethod
    def update_position(position_id: str, request: PositionUpdate) -> Position:
        payload = request.model_dump(exclude_unset=True)
        if not payload:
            return BusinessService.get_position(position_id)

        assignments = ", ".join(f"{key} = %s" for key in payload)
        values = list(payload.values())
        values.append(position_id)
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    UPDATE positions
                    SET {assignments}, updated_at = now()
                    WHERE position_id = %s
                    RETURNING *
                    """,
                    values,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise ValueError(f"Position not found: {position_id}")
        return Position(**row)

    @staticmethod
    def get_position(position_id: str) -> Position:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT * FROM positions WHERE position_id = %s", (position_id,))
                row = cur.fetchone()
        if row is None:
            raise ValueError(f"Position not found: {position_id}")
        return Position(**row)

    @staticmethod
    def create_exit_alert(request: ExitAlertCreate) -> ExitAlert:
        alert_id = request.alert_id or f"alert_{uuid4().hex}"
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO exit_alerts (
                        alert_id, position_id, level, action, reason, new_stop,
                        triggered_rules, acknowledged
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        alert_id,
                        request.position_id,
                        request.level,
                        request.action,
                        request.reason,
                        request.new_stop,
                        request.triggered_rules,
                        request.acknowledged,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return ExitAlert(**row)

    @staticmethod
    def list_exit_alerts(acknowledged: bool | None = None, limit: int = 100) -> list[ExitAlert]:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if acknowledged is None:
                    cur.execute(
                        "SELECT * FROM exit_alerts ORDER BY alert_ts DESC LIMIT %s",
                        (limit,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT *
                        FROM exit_alerts
                        WHERE acknowledged = %s
                        ORDER BY alert_ts DESC
                        LIMIT %s
                        """,
                        (acknowledged, limit),
                    )
                rows = list(cur.fetchall())
        return [ExitAlert(**row) for row in rows]

    @staticmethod
    def update_exit_alert(alert_id: str, request: ExitAlertUpdate) -> ExitAlert:
        payload = request.model_dump(exclude_unset=True)
        if not payload:
            return BusinessService.get_exit_alert(alert_id)

        assignments = ", ".join(f"{key} = %s" for key in payload)
        values = list(payload.values())
        values.append(alert_id)
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"UPDATE exit_alerts SET {assignments} WHERE alert_id = %s RETURNING *",
                    values,
                )
                row = cur.fetchone()
            conn.commit()
        if row is None:
            raise ValueError(f"Exit alert not found: {alert_id}")
        return ExitAlert(**row)

    @staticmethod
    def get_exit_alert(alert_id: str) -> ExitAlert:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT * FROM exit_alerts WHERE alert_id = %s", (alert_id,))
                row = cur.fetchone()
        if row is None:
            raise ValueError(f"Exit alert not found: {alert_id}")
        return ExitAlert(**row)

    @staticmethod
    def create_journal_trade(request: JournalTradeCreate) -> JournalTrade:
        trade_id = request.trade_id or f"trade_{uuid4().hex}"
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO trades_journal (
                        trade_id, position_id, symbol_id, entry_ts, exit_ts,
                        entry_price, exit_price, quantity, gross_pnl, net_pnl,
                        r_multiple, setup_type, exit_reason, mistake_tags, notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        trade_id,
                        request.position_id,
                        request.symbol_id,
                        request.entry_ts,
                        request.exit_ts,
                        request.entry_price,
                        request.exit_price,
                        request.quantity,
                        request.gross_pnl,
                        request.net_pnl,
                        request.r_multiple,
                        request.setup_type,
                        request.exit_reason,
                        request.mistake_tags,
                        request.notes,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return JournalTrade(**row)

    @staticmethod
    def list_journal_trades(limit: int = 100) -> list[JournalTrade]:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT * FROM trades_journal ORDER BY entry_ts DESC NULLS LAST LIMIT %s",
                    (limit,),
                )
                rows = list(cur.fetchall())
        return [JournalTrade(**row) for row in rows]

    @staticmethod
    def dashboard_summary() -> DashboardSummary:
        with connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT count(*) AS count FROM candidates")
                candidate_count = cur.fetchone()["count"]
                cur.execute("SELECT count(*) AS count FROM positions WHERE status = 'open'")
                open_position_count = cur.fetchone()["count"]
                cur.execute(
                    """
                    SELECT count(*) AS count, max(level) AS highest_level
                    FROM exit_alerts
                    WHERE acknowledged = false
                    """
                )
                alert_summary = cur.fetchone()
                cur.execute(
                    """
                    SELECT snapshot_ts, risk_level, us_bias, japan_bias, notes
                    FROM market_context_snapshots
                    ORDER BY snapshot_ts DESC
                    LIMIT 1
                    """
                )
                market_context = cur.fetchone()
                cur.execute(
                    """
                    SELECT dataset_key, last_updated_at, source
                    FROM data_freshness
                    ORDER BY dataset_key
                    """
                )
                freshness_rows = list(cur.fetchall())

        context = (
            MarketContextSummary(**market_context)
            if market_context
            else MarketContextSummary(risk_level="unknown")
        )
        return DashboardSummary(
            market_context=context,
            risk_mode=context.risk_level or "unknown",
            candidate_count=candidate_count,
            open_position_count=open_position_count,
            exit_alert_count=alert_summary["count"],
            highest_exit_level=alert_summary["highest_level"],
            data_freshness=[DataFreshnessSummary(**row) for row in freshness_rows],
        )
