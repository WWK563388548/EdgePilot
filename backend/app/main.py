from fastapi import FastAPI

from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.ingestion import router as ingestion_router
from backend.app.api.routes.realtime import router as realtime_router
from backend.app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(analytics_router)
app.include_router(realtime_router)
app.include_router(ingestion_router)
