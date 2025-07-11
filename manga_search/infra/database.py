import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
import logging


logger = logging.getLogger(__name__)


# Database URL - adjust according to your setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost:5432/postgres"
)


# Create async engine with optimized settings
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "server_settings": {
            "jit": "off",  # Disable JIT for better connection speed
        }
    }
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False  # Manual flush control for better performance
)

# Base class for models
Base = declarative_base()
metadata = MetaData()

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
