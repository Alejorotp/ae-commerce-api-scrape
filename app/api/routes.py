from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
import json

from app.database import get_db
from app.models import Garment
from app.schemas import GarmentResponse, PaginatedGarments, ColorimetryEnum
from app.config import settings
from app.services.scraper import run_scraper
from app.services.storage import get_presigned_url
from app.services.cloudinary_service import upload_image
from app.services.replicate_service import generate_tryon_flux, generate_tryon_nano

router = APIRouter()

@router.get("/garments", response_model=PaginatedGarments)
async def get_garments(
    name: Optional[str] = None,
    category: Optional[str] = None,
    gender: Optional[str] = None,
    color: Optional[str] = None,
    colorimetry: Optional[ColorimetryEnum] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Garment)
    
    if name:
        stmt = stmt.where(func.similarity(Garment.name, name) > 0.2)
        stmt = stmt.order_by(func.similarity(Garment.name, name).desc())
    if category:
        stmt = stmt.where(func.similarity(Garment.category, category) > 0.2)
        stmt = stmt.order_by(func.similarity(Garment.category, category).desc())
    if gender:
        stmt = stmt.where(Garment.gender == gender)
    if color:
        stmt = stmt.where(Garment.color == color)
    if colorimetry:
        stmt = stmt.where(Garment.colorimetry == colorimetry.value)
        
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # Pagination
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    signed_items = []
    for item in items:
        resp = GarmentResponse.model_validate(item)
        signed_images = []
        for img in item.images:
            key = img.split("/")[-1]
            s_url = await get_presigned_url(key)
            signed_images.append(s_url if s_url else img)
        resp.images = signed_images
        signed_items.append(resp)
    
    pages = (total + size - 1) // size
    
    return PaginatedGarments(
        items=signed_items,
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
        
    resp = GarmentResponse.model_validate(garment)
    signed_images = []
    for img in garment.images:
        key = img.split("/")[-1]
        s_url = await get_presigned_url(key)
        signed_images.append(s_url if s_url else img)
    resp.images = signed_images
    
    return resp

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
    
@router.get("/image-url")
async def get_image_url(url: str = Query(..., description="The full S3 image URL from the database")):
    """Generate a presigned URL from a full image URL."""
    # Extract the key from the URL (the last part after the last slash)
    image_key = url.split("/")[-1]
    
    presigned_url = await get_presigned_url(image_key)
    if not presigned_url:
        raise HTTPException(status_code=500, detail="Failed to generate URL")
    return {"url": presigned_url}

@router.post("/generate")
async def generate_outfits(
    person_image: UploadFile = File(...),
    product_urls: str = Form(...)
):
    print("NEW ENDPOINT LOADED")
    parsed_urls = json.loads(product_urls)
    if not isinstance(parsed_urls, list):
        return {
        "error": "product_urls must be a list"
        }

    person_image_url = upload_image(person_image.file)

    generated_images = []

    for product_url in parsed_urls:

        try:
            print(f"Generating for: {product_url}")
            result_url = generate_tryon_nano(
            person_image_url,
            product_url
            )

            generated_images.append(result_url)

        except Exception as e:
            generated_images.append({
            "product": product_url,
            "error": str(e)
            })

    return {
        "results": generated_images
    }

@router.post("/generate-single")
async def generate_single_outfit(
    person_image_url: str = Form(...),
    product_image: UploadFile = File(...)
):

    try:
        product_image_url = upload_image(product_image.file)
        
        result_url = generate_tryon_nano(
            person_image_url,
            product_image_url
        )

        return {
            "result": result_url
        }

    except Exception as e:

        return {
            "error": str(e)
        }
        
@router.post("/upload-person")
async def upload_person_image(
    person_image: UploadFile = File(...)
):

    try:

        person_image_url = upload_image(
            person_image.file
        )

        return {
            "person_image_url": person_image_url
        }

    except Exception as e:

        return {
            "error": str(e)
        }