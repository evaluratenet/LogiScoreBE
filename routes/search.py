from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from database.database import get_db
from database.models import FreightForwarder, Review, Branch

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    name: str
    website: Optional[str]
    logo_url: Optional[str]
    description: Optional[str]
    headquarters: Optional[str]
    average_rating: Optional[float]
    review_count: int
    is_verified: bool

    class Config:
        from_attributes = True

@router.get("/freight-forwarders", response_model=List[SearchResult])
async def search_freight_forwarders(
    q: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Search freight forwarders with filters"""
    
    # Build base query with average rating and review count
    query = db.query(
        FreightForwarder,
        func.avg(Review.overall_rating).label('average_rating'),
        func.count(Review.id).label('review_count')
    ).outerjoin(Review, FreightForwarder.id == Review.freight_forwarder_id)\
     .filter(FreightForwarder.is_active == True)\
     .group_by(FreightForwarder.id)
    
    # Apply search filter
    if q:
        query = query.filter(
            FreightForwarder.name.ilike(f"%{q}%") |
            FreightForwarder.description.ilike(f"%{q}%") |
            FreightForwarder.headquarters.ilike(f"%{q}%") |
            FreightForwarder.services.ilike(f"%{q}%")
        )
    
    # Apply location filter
    if location:
        query = query.filter(
            FreightForwarder.headquarters.ilike(f"%{location}%")
        )
    
    # Apply rating filter
    if min_rating is not None:
        query = query.having(func.avg(Review.overall_rating) >= min_rating)
    
    # Order by rating (descending) and then by name
    query = query.order_by(
        func.avg(Review.overall_rating).desc().nullslast(),
        FreightForwarder.name.asc()
    )
    
    # Apply pagination
    results = query.offset(skip).limit(limit).all()
    
    # Convert to response format
    search_results = []
    for freight_forwarder, avg_rating, review_count in results:
        result = SearchResult(
            id=str(freight_forwarder.id),
            name=freight_forwarder.name,
            website=freight_forwarder.website,
            logo_url=freight_forwarder.logo_url,
            description=freight_forwarder.description,
            headquarters=freight_forwarder.headquarters,
            average_rating=float(avg_rating) if avg_rating else None,
            review_count=review_count,
            is_verified=freight_forwarder.is_verified
        )
        search_results.append(result)
    
    return search_results

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get search suggestions for freight forwarder names"""
    
    suggestions = db.query(FreightForwarder.name)\
        .filter(
            FreightForwarder.name.ilike(f"%{q}%"),
            FreightForwarder.is_active == True
        )\
        .limit(limit)\
        .all()
    
    return [suggestion[0] for suggestion in suggestions] 