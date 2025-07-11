from fastapi import APIRouter, HTTPException, Depends
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import MangaLinkCreate, MangaLink as MangaLinkSchema
from ..services.crud import MangaLinkCRUD


router = APIRouter(prefix="/manga", tags=["manga-links"])


@router.get("/{manga_id}/links", response_model=List[MangaLinkSchema])
async def get_manga_links(manga_id: int, db: AsyncSession = Depends(get_db)):
    """Get all links for a manga"""
    return await MangaLinkCRUD.get_manga_links(db, manga_id)

@router.post("/links", response_model=MangaLinkSchema)
async def create_manga_link(link: MangaLinkCreate, db: AsyncSession = Depends(get_db)):
    """Create a new manga link"""
    return await MangaLinkCRUD.create_manga_link(db, link)

@router.get("/links/{link_id}", response_model=MangaLinkSchema)
async def get_manga_link(link_id: int, db: AsyncSession = Depends(get_db)):
    """Get link by ID"""
    link = await MangaLinkCRUD.get_manga_link(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@router.put("/links/{link_id}", response_model=MangaLinkSchema)
async def update_manga_link(link_id: int, link: MangaLinkCreate, db: AsyncSession = Depends(get_db)):
    """Update manga link"""
    updated_link = await MangaLinkCRUD.update_manga_link(db, link_id, link)
    if not updated_link:
        raise HTTPException(status_code=404, detail="Link not found")
    return updated_link

@router.delete("/links/{link_id}")
async def delete_manga_link(link_id: int, db: AsyncSession = Depends(get_db)):
    """Delete manga link"""
    deleted = await MangaLinkCRUD.delete_manga_link(db, link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"message": "Link deleted successfully"}
