from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import GenreCreate, Genre as GenreSchema
from ..services.crud import GenreCRUD


router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=List[GenreSchema])
async def get_genres(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of genres"""
    return await GenreCRUD.get_genres(db, skip, limit, search)

@router.get("/count")
async def get_genres_count(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get total count of genres"""
    count = await GenreCRUD.get_genres_count(db, search)
    return {"total_count": count}

@router.get("/popular")
async def get_popular_genres(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get popular genres ordered by manga count and rating"""
    return await GenreCRUD.get_popular_genres(db, limit)

@router.post("", response_model=GenreSchema)
async def create_genre(genre: GenreCreate, db: AsyncSession = Depends(get_db)):
    """Create a new genre"""
    return await GenreCRUD.create_genre(db, genre)

@router.get("/{genre_id}", response_model=GenreSchema)
async def get_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    """Get genre by ID"""
    genre = await GenreCRUD.get_genre(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre

@router.put("/{genre_id}", response_model=GenreSchema)
async def update_genre(genre_id: int, genre: GenreCreate, db: AsyncSession = Depends(get_db)):
    """Update genre"""
    updated_genre = await GenreCRUD.update_genre(db, genre_id, genre)
    if not updated_genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return updated_genre

@router.delete("/{genre_id}")
async def delete_genre(genre_id: int, db: AsyncSession = Depends(get_db)):
    """Delete genre"""
    deleted = await GenreCRUD.delete_genre(db, genre_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete genre with manga relationships")
    return {"message": "Genre deleted successfully"}

@router.get("/{genre_id}/manga-count")
async def get_genre_manga_count(genre_id: int, db: AsyncSession = Depends(get_db)):
    """Get count of manga for this genre"""
    count = await GenreCRUD.get_genre_manga_count(db, genre_id)
    return {"manga_count": count}
