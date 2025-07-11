from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import ArtistCreate, Artist as ArtistSchema
from ..services.crud import ArtistCRUD


router = APIRouter(prefix="/artists", tags=["artists"])


@router.get("", response_model=List[ArtistSchema])
async def get_artists(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of artists"""
    return await ArtistCRUD.get_artists(db, skip, limit, search)

@router.get("/count")
async def get_artists_count(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get total count of artists"""
    count = await ArtistCRUD.get_artists_count(db, search)
    return {"total_count": count}

@router.post("", response_model=ArtistSchema)
async def create_artist(artist: ArtistCreate, db: AsyncSession = Depends(get_db)):
    """Create a new artist"""
    return await ArtistCRUD.create_artist(db, artist)

@router.get("/{artist_id}", response_model=ArtistSchema)
async def get_artist(artist_id: int, db: AsyncSession = Depends(get_db)):
    """Get artist by ID"""
    artist = await ArtistCRUD.get_artist(db, artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist

@router.put("/{artist_id}", response_model=ArtistSchema)
async def update_artist(artist_id: int, artist: ArtistCreate, db: AsyncSession = Depends(get_db)):
    """Update artist"""
    updated_artist = await ArtistCRUD.update_artist(db, artist_id, artist)
    if not updated_artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return updated_artist

@router.delete("/{artist_id}")
async def delete_artist(artist_id: int, db: AsyncSession = Depends(get_db)):
    """Delete artist"""
    deleted = await ArtistCRUD.delete_artist(db, artist_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete artist with manga relationships")
    return {"message": "Artist deleted successfully"}

@router.get("/{artist_id}/manga-count")
async def get_artist_manga_count(artist_id: int, db: AsyncSession = Depends(get_db)):
    """Get count of manga for this artist"""
    count = await ArtistCRUD.get_artist_manga_count(db, artist_id)
    return {"manga_count": count}
