from backend.app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def sqlalchemy_database_url() -> str:
    if settings.database_url.startswith("postgresql+psycopg://"):
        return settings.database_url
    return settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)


class Base(DeclarativeBase):
    pass


engine = create_engine(sqlalchemy_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    with SessionLocal() as session:
        yield session


DbSession = Session
