from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..services.crud import StatisticsCRUD


router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("")
async def get_database_stats(db: AsyncSession = Depends(get_db)):
    """Get overall database statistics"""
    return await StatisticsCRUD.get_database_stats(db)

@router.get("/year-distribution")
async def get_year_distribution(db: AsyncSession = Depends(get_db)):
    """Get manga distribution by year"""
    return await StatisticsCRUD.get_year_distribution(db)

@router.get("/rating-distribution")
async def get_rating_distribution(db: AsyncSession = Depends(get_db)):
    """Get manga distribution by rating ranges"""
    return await StatisticsCRUD.get_rating_distribution(db)
