"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL_RAW = os.getenv("DATABASE_URL", "")

if DATABASE_URL_RAW:
    if DATABASE_URL_RAW.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL_RAW.replace("postgres://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL_RAW.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL_RAW.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = DATABASE_URL_RAW
else:
    DATABASE_URL = "sqlite+aiosqlite:///./docfinder.db"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Get database session."""
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Check and add file_path column if missing (self-healing migration)
    from sqlalchemy import text
    async with engine.begin() as conn:
        try:
            await conn.execute(text("SELECT file_path FROM uploaded_files LIMIT 1"))
        except Exception:
            try:
                await conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN file_path VARCHAR(500)"))
                print("Database migrated: Added file_path column to uploaded_files table.")
            except Exception as e:
                print(f"Warning during DB file_path migration: {e}")