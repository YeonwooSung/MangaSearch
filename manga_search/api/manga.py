from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import logging
import io
import csv

from sqlalchemy.ext.asyncio import AsyncSession

from ..infra.database import get_db
from ..model.schemas import (
    MangaCreate, MangaUpdate, Manga as MangaSchema
)
from ..services.crud import MangaCRUD


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manga", tags=["manga"])


@router.get("/{manga_id}", response_model=MangaSchema)
async def get_manga(manga_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific manga by ID with all related data"""
    manga = await MangaCRUD.get_manga(db, manga_id)
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    return manga

@router.get("", response_model=List[MangaSchema])
async def get_manga_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: Optional[Decimal] = None,
    max_rating: Optional[Decimal] = None,
    content_rating: Optional[str] = None,
    manga_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of manga with optional filters"""
    manga_list = await MangaCRUD.get_manga_list(
        db, skip, limit, status, year, min_rating, max_rating, content_rating, manga_type
    )
    return manga_list

@router.get("/count")
async def get_manga_count(
    status: Optional[str] = None,
    year: Optional[int] = None,
    min_rating: Optional[Decimal] = None,
    max_rating: Optional[Decimal] = None,
    content_rating: Optional[str] = None,
    manga_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get total count of manga matching filters"""
    count = await MangaCRUD.get_manga_count(
        db, status, year, min_rating, max_rating, content_rating, manga_type
    )
    return {"total_count": count}

@router.post("", response_model=MangaSchema)
async def create_manga(manga: MangaCreate, db: AsyncSession = Depends(get_db)):
    """Create a new manga"""
    return await MangaCRUD.create_manga(db, manga)

@router.put("/{manga_id}", response_model=MangaSchema)
async def update_manga(manga_id: int, manga: MangaUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing manga"""
    updated_manga = await MangaCRUD.update_manga(db, manga_id, manga)
    if not updated_manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    return updated_manga

@router.delete("/{manga_id}")
async def delete_manga(manga_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a manga"""
    deleted = await MangaCRUD.delete_manga(db, manga_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Manga not found")
    return {"message": "Manga deleted successfully"}

@router.post("/bulk", response_model=List[MangaSchema])
async def create_bulk_manga(
    manga_list: List[MangaCreate], 
    db: AsyncSession = Depends(get_db)
):
    """Create multiple manga in bulk - optimized for large datasets"""
    created_manga = []
    
    try:
        for manga_data in manga_list:
            manga = await MangaCRUD.create_manga(db, manga_data)
            created_manga.append(manga)
        
        logger.info(f"Created {len(created_manga)} manga records in bulk")
        return created_manga
        
    except Exception as e:
        logger.error(f"Bulk creation failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Bulk creation failed: {str(e)}"
        )

@router.get("/bulk/export")
async def export_manga_bulk(
    limit: int = Query(1000, le=10000),
    offset: int = Query(0, ge=0),
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db)
):
    """Export manga data in bulk - demonstrates orjson performance with large datasets"""
    
    if format == "csv":
        # Get data
        manga_list = await MangaCRUD.get_manga_list(db, offset, limit)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['id', 'title', 'native_title', 'year', 'rating', 'status'])
        
        # Data
        for manga in manga_list:
            writer.writerow([
                manga.id, manga.title, manga.native_title, 
                manga.year, manga.rating, manga.status
            ])
        
        response = StreamingResponse(
            io.BytesIO(output.getvalue().encode()), 
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=manga_export.csv"
        return response
    
    else:
        # JSON export using orjson (default)
        manga_list = await MangaCRUD.get_manga_list(db, offset, limit)
        
        # Add metadata for large datasets
        export_data = {
            "metadata": {
                "total_exported": len(manga_list),
                "offset": offset,
                "limit": limit,
                "export_timestamp": datetime.utcnow().isoformat()
            },
            "data": [manga.__dict__ for manga in manga_list]
        }
        
        return export_data
