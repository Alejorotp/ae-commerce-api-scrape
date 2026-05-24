from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class Garment(Base):
    __tablename__ = "garments"

    id = Column(String, primary_key=True, index=True)
    link = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    color = Column(String, nullable=True)
    colorimetry = Column(String, nullable=True)
    fabric = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    # Store dynamic sizes and stock as JSONB (Postgres JSON type)
    # [{"size": "XS", "in_stock": True}, {"size": "S", "in_stock": False}]
    sizes_stock = Column(JSON, default=list)
    
    # Store image URLs as a list of strings in JSON
    # ["https://bucket/img1.jpg", "https://bucket/img2.jpg"]
    images = Column(JSON, default=list)
    
    metadata_field = Column(JSON, default=dict)
    
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
