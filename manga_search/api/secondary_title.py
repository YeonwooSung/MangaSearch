from fastapi import APIRouter, HTTPException, Depends
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import MangaSecondaryTitleCreate, MangaSecondaryTitle as MangaSecondaryTitleSchema
from ..services.crud import MangaSecondaryTitleCRUD

router = APIRouter(prefix="/manga", tags=["manga-secondary-titles"])

@router.get("/{manga_id}/secondary-titles", response_model=List[MangaSecondaryTitleSchema])
async def get_manga_secondary_titles(manga_id: int, db: AsyncSession = Depends(get_db)):
    """Get all secondary titles for a manga"""
    return await MangaSecondaryTitleCRUD.get_manga_secondary_titles(db, manga_id)

@router.post("/secondary-titles", response_model=MangaSecondaryTitleSchema)
async def create_manga_secondary_title(title: MangaSecondaryTitleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new manga secondary title"""
    return await MangaSecondaryTitleCRUD.create_manga_secondary_title(db, title)

@router.get("/secondary-titles/{title_id}", response_model=MangaSecondaryTitleSchema)
async def get_manga_secondary_title(title_id: int, db: AsyncSession = Depends(get_db)):
    """Get secondary title by ID"""
    title = await MangaSecondaryTitleCRUD.get_manga_secondary_title(db, title_id)
    if not title:
        raise HTTPException(status_code=404, detail="Secondary title not found")
    return title

@router.put("/secondary-titles/{title_id}", response_model=MangaSecondaryTitleSchema)
async def update_manga_secondary_title(title_id: int, title: MangaSecondaryTitleCreate, db: AsyncSession = Depends(get_db)):
    """Update manga secondary title"""
    updated_title = await MangaSecondaryTitleCRUD.update_manga_secondary_title(db, title_id, title)
    if not updated_title:
        raise HTTPException(status_code=404, detail="Secondary title not found")
    return updated_title

@router.delete("/secondary-titles/{title_id}")
async def delete_manga_secondary_title(title_id: int, db: AsyncSession = Depends(get_db)):
    """Delete manga secondary title"""
    deleted = await MangaSecondaryTitleCRUD.delete_manga_secondary_title(db, title_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Secondary title not found")
    return {"message": "Secondary title deleted successfully"}
