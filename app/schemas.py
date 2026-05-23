from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class SizeStockSchema(BaseModel):
    size: str
    in_stock: bool

class GarmentBase(BaseModel):
    id: str
    link: str
    name: str
    category: Optional[str] = None
    gender: Optional[str] = None
    color: Optional[str] = None
    fabric: Optional[str] = None
    description: Optional[str] = None
    sizes_stock: List[SizeStockSchema] = []
    images: List[str] = []
    metadata_field: dict = {}

class GarmentResponse(GarmentBase):
    scraped_at: datetime

    class Config:
        from_attributes = True

class PaginatedGarments(BaseModel):
    items: List[GarmentResponse]
    total: int
    page: int
    size: int
    pages: int
