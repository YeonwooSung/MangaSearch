from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import AuthorCreate, Author as AuthorSchema
from ..services.crud import AuthorCRUD


router = APIRouter(prefix="/authors", tags=["authors"])


@router.get("", response_model=List[AuthorSchema])
async def get_authors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of authors"""
    return await AuthorCRUD.get_authors(db, skip, limit, search)

@router.get("/count")
async def get_authors_count(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get total count of authors"""
    count = await AuthorCRUD.get_authors_count(db, search)
    return {"total_count": count}

@router.post("", response_model=AuthorSchema)
async def create_author(author: AuthorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new author"""
    return await AuthorCRUD.create_author(db, author)

@router.get("/{author_id}", response_model=AuthorSchema)
async def get_author(author_id: int, db: AsyncSession = Depends(get_db)):
    """Get author by ID"""
    author = await AuthorCRUD.get_author(db, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

@router.put("/{author_id}", response_model=AuthorSchema)
async def update_author(author_id: int, author: AuthorCreate, db: AsyncSession = Depends(get_db)):
    """Update author"""
    updated_author = await AuthorCRUD.update_author(db, author_id, author)
    if not updated_author:
        raise HTTPException(status_code=404, detail="Author not found")
    return updated_author

@router.delete("/{author_id}")
async def delete_author(author_id: int, db: AsyncSession = Depends(get_db)):
    """Delete author"""
    deleted = await AuthorCRUD.delete_author(db, author_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete author with manga relationships")
    return {"message": "Author deleted successfully"}

@router.get("/{author_id}/manga-count")
async def get_author_manga_count(author_id: int, db: AsyncSession = Depends(get_db)):
    """Get count of manga for this author"""
    count = await AuthorCRUD.get_author_manga_count(db, author_id)
    return {"manga_count": count}
