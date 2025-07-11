from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .infra.database import engine, AsyncSessionLocal, get_db

# Import all routers
from .api import (
    manga, author, artist, publisher, genre, tag,
    cover, secondary_title, link, search, stats
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("🚀 Starting up Manga Database API...")
    try:
        # Test database connection
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✅ Database connection established successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Manga Database API...")
    try:
        # Close database connections
        await engine.dispose()
        logger.info("✅ Database connections closed successfully")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


app = FastAPI(
    title="Manga Database API",
    description="FastAPI CRUD application for ParadeDB-based Manga database with BM25 search",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"]
)

# Register all routers
app.include_router(manga.router)
app.include_router(author.router)
app.include_router(artist.router)
app.include_router(publisher.router)
app.include_router(genre.router)
app.include_router(tag.router)
app.include_router(cover.router)
app.include_router(secondary_title.router)
app.include_router(link.router)
app.include_router(search.router)
app.include_router(stats.router)


# Health check endpoint (kept in main for simplicity)
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint with database status"""
    try:
        # Simple query to test database connection
        result = await db.execute(text("SELECT 1"))
        logger.info(f"Health check passed: {result.scalar()}")

        # Additional database info
        db_info = await db.execute(text("""
            SELECT 
                current_database() as database_name,
                version() as version,
                current_timestamp as server_time
        """))
        db_data = db_info.fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "database_name": db_data.database_name,
            "server_time": db_data.server_time.isoformat(),
            "api_version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("manga_search.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
