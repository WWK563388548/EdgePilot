import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.app.core.config import settings

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


def _sse_encode(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _event_stream():
    while True:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "event_type": "system.heartbeat",
            "severity": "P3",
            "created_at": now,
            "message": "EdgePilot realtime stream alive",
        }
        yield _sse_encode(payload)
        await asyncio.sleep(settings.sse_heartbeat_seconds)


@router.get("/events/stream")
def stream_events() -> StreamingResponse:
    return StreamingResponse(_event_stream(), media_type="text/event-stream")
