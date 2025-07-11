from fastapi import APIRouter, HTTPException, Depends
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import MangaCoverCreate, MangaCover as MangaCoverSchema
from ..services.crud import MangaCoverCRUD


router = APIRouter(prefix="/manga", tags=["manga-covers"])


@router.get("/{manga_id}/covers", response_model=List[MangaCoverSchema])
async def get_manga_covers(manga_id: int, db: AsyncSession = Depends(get_db)):
    """Get all covers for a manga"""
    return await MangaCoverCRUD.get_manga_covers(db, manga_id)

@router.post("/covers", response_model=MangaCoverSchema)
async def create_manga_cover(cover: MangaCoverCreate, db: AsyncSession = Depends(get_db)):
    """Create a new manga cover"""
    return await MangaCoverCRUD.create_manga_cover(db, cover)

@router.get("/covers/{cover_id}", response_model=MangaCoverSchema)
async def get_manga_cover(cover_id: int, db: AsyncSession = Depends(get_db)):
    """Get cover by ID"""
    cover = await MangaCoverCRUD.get_manga_cover(db, cover_id)
    if not cover:
        raise HTTPException(status_code=404, detail="Cover not found")
    return cover

@router.put("/covers/{cover_id}", response_model=MangaCoverSchema)
async def update_manga_cover(cover_id: int, cover: MangaCoverCreate, db: AsyncSession = Depends(get_db)):
    """Update manga cover"""
    updated_cover = await MangaCoverCRUD.update_manga_cover(db, cover_id, cover)
    if not updated_cover:
        raise HTTPException(status_code=404, detail="Cover not found")
    return updated_cover

@router.delete("/covers/{cover_id}")
async def delete_manga_cover(cover_id: int, db: AsyncSession = Depends(get_db)):
    """Delete manga cover"""
    deleted = await MangaCoverCRUD.delete_manga_cover(db, cover_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cover not found")
    return {"message": "Cover deleted successfully"}
