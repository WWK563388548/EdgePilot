from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.analytics import router as analytics_router
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.business import router as business_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.ingestion import router as ingestion_router
from backend.app.api.routes.pa import router as pa_router
from backend.app.api.routes.realtime import router as realtime_router
from backend.app.api.routes.tenant import router as tenant_router
from backend.app.core.config import settings

app = FastAPI(title=settings.app_name)

cors_origins = [
    origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(realtime_router)
app.include_router(tenant_router)
app.include_router(ingestion_router)
app.include_router(pa_router)
app.include_router(business_router)
