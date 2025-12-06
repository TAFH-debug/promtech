from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings

from app.models import Object, Diagnostic

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


def init_db():
    """Initialize database - create all tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session

