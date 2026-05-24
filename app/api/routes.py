from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional

from app.database import get_db
from app.models import Garment
from app.schemas import GarmentResponse, PaginatedGarments
from app.config import settings
from app.services.scraper import run_scraper
from app.services.storage import get_presigned_url

router = APIRouter()

@router.get("/garments", response_model=PaginatedGarments)
async def get_garments(
    category: Optional[str] = None,
    gender: Optional[str] = None,
    color: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Garment)
    
    if category:
        stmt = stmt.where(Garment.category == category)
    if gender:
        stmt = stmt.where(Garment.gender == gender)
    if color:
        stmt = stmt.where(Garment.color == color)
        
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # Pagination
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    pages = (total + size - 1) // size
    
    return PaginatedGarments(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get("/garments/{garment_id}", response_model=GarmentResponse)
async def get_garment(garment_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Garment).where(Garment.id == garment_id)
    result = await db.execute(stmt)
    garment = result.scalars().first()
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    return garment

@router.get("/categories", response_model=List[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    stmt = select(Garment.category).distinct()
    result = await db.execute(stmt)
    return [r for r in result.scalars().all() if r]

@router.get("/categories/{category_name}/colors", response_model=List[str])
async def get_category_colors(category_name: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Garment.color).where(Garment.category == category_name).distinct()
    result = await db.execute(stmt)
    return [r for r in result.scalars().all() if r]

@router.post("/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, x_scrape_password: str = Header(...)):
    if x_scrape_password != settings.scrape_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    background_tasks.add_task(run_scraper)
    return {"message": "Scraping process initiated in the background."}
@router.get("/image-url/{image_key}")
async def get_image_url(image_key: str):
    """Generate a presigned URL for an image."""
    url = await get_presigned_url(image_key)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to generate URL")
    return {"url": url}
