from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import TagCreate, Tag as TagSchema
from ..services.crud import TagCRUD


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[TagSchema])
async def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of tags"""
    return await TagCRUD.get_tags(db, skip, limit, search)

@router.get("/count")
async def get_tags_count(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get total count of tags"""
    count = await TagCRUD.get_tags_count(db, search)
    return {"total_count": count}

@router.get("/popular")
async def get_popular_tags(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get popular tags ordered by manga count and rating"""
    return await TagCRUD.get_popular_tags(db, limit)

@router.post("", response_model=TagSchema)
async def create_tag(tag: TagCreate, db: AsyncSession = Depends(get_db)):
    """Create a new tag"""
    return await TagCRUD.create_tag(db, tag)

@router.get("/{tag_id}", response_model=TagSchema)
async def get_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Get tag by ID"""
    tag = await TagCRUD.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/{tag_id}", response_model=TagSchema)
async def update_tag(tag_id: int, tag: TagCreate, db: AsyncSession = Depends(get_db)):
    """Update tag"""
    updated_tag = await TagCRUD.update_tag(db, tag_id, tag)
    if not updated_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return updated_tag

@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Delete tag"""
    deleted = await TagCRUD.delete_tag(db, tag_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete tag with manga relationships")
    return {"message": "Tag deleted successfully"}

@router.get("/{tag_id}/manga-count")
async def get_tag_manga_count(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Get count of manga for this tag"""
    count = await TagCRUD.get_tag_manga_count(db, tag_id)
    return {"manga_count": count}
