from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import PublisherCreate, Publisher as PublisherSchema
from ..services.crud import PublisherCRUD


router = APIRouter(prefix="/publishers", tags=["publishers"])


@router.get("", response_model=List[PublisherSchema])
async def get_publishers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of publishers"""
    return await PublisherCRUD.get_publishers(db, skip, limit, search)

@router.get("/count")
async def get_publishers_count(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get total count of publishers"""
    count = await PublisherCRUD.get_publishers_count(db, search)
    return {"total_count": count}

@router.post("", response_model=PublisherSchema)
async def create_publisher(publisher: PublisherCreate, db: AsyncSession = Depends(get_db)):
    """Create a new publisher"""
    return await PublisherCRUD.create_publisher(db, publisher)

@router.get("/{publisher_id}", response_model=PublisherSchema)
async def get_publisher(publisher_id: int, db: AsyncSession = Depends(get_db)):
    """Get publisher by ID"""
    publisher = await PublisherCRUD.get_publisher(db, publisher_id)
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return publisher

@router.put("/{publisher_id}", response_model=PublisherSchema)
async def update_publisher(publisher_id: int, publisher: PublisherCreate, db: AsyncSession = Depends(get_db)):
    """Update publisher"""
    updated_publisher = await PublisherCRUD.update_publisher(db, publisher_id, publisher)
    if not updated_publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return updated_publisher

@router.delete("/{publisher_id}")
async def delete_publisher(publisher_id: int, db: AsyncSession = Depends(get_db)):
    """Delete publisher"""
    deleted = await PublisherCRUD.delete_publisher(db, publisher_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete publisher with manga relationships")
    return {"message": "Publisher deleted successfully"}

@router.get("/{publisher_id}/manga-count")
async def get_publisher_manga_count(publisher_id: int, db: AsyncSession = Depends(get_db)):
    """Get count of manga for this publisher"""
    count = await PublisherCRUD.get_publisher_manga_count(db, publisher_id)
    return {"manga_count": count}
