from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database.database import get_db
from database.models import FreightForwarder

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    name: str
    website: Optional[str]
    logo_url: Optional[str]

    class Config:
        from_attributes = True

@router.get("/freight-forwarders", response_model=List[SearchResult])
async def search_freight_forwarders(
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    db: Session = Depends(get_db)
):
    """Search freight forwarders by name"""
    
    query = db.query(FreightForwarder)
    
    if q:
        query = query.filter(FreightForwarder.name.ilike(f"%{q}%"))
    
    results = query.limit(limit).all()
    
    return [
        SearchResult(
            id=str(ff.id),
            name=ff.name,
            website=ff.website,
            logo_url=ff.logo_url
        ) for ff in results
    ]

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get search suggestions for freight forwarder names"""
    
    suggestions = db.query(FreightForwarder.name)\
        .filter(FreightForwarder.name.ilike(f"%{q}%"))\
        .limit(limit)\
        .all()
    
    return [suggestion[0] for suggestion in suggestions] 