from backend.app.core.config import settings


def psycopg_database_url() -> str:
    return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect():
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError("psycopg is required for database access") from exc

    return psycopg.connect(psycopg_database_url())
