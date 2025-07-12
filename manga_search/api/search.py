from fastapi import APIRouter, Depends, Query
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..infra.database import get_db
from ..model.schemas import SearchParams, MangaSearchResult
from ..services.crud import MangaCRUD


router = APIRouter(prefix="/manga/search", tags=["search"])


@router.post("", response_model=List[MangaSearchResult])
async def search_manga(params: SearchParams, db: AsyncSession = Depends(get_db)):
    """Basic BM25 search for manga"""
    return await MangaCRUD.search_manga(db, params)


@router.post("/advanced")
async def advanced_search_manga(params: SearchParams, db: AsyncSession = Depends(get_db)):
    """Advanced search with filters using the database function"""
    return await MangaCRUD.advanced_search_manga(db, params)


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions for auto-complete"""
    # Simple title-based suggestions
    sql = text("""
        SELECT m.id, m.title, m.native_title,
               paradedb.score(m.id) as relevance_score
        FROM manga m
        WHERE m.title_search @@@ :query
        ORDER BY paradedb.score(m.id) DESC
        LIMIT :limit
    """)
    
    result = await db.execute(sql, {'query': query, 'limit': limit})
    return [dict(row._mapping) for row in result.fetchall()]
