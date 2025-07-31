from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database.database import get_db
from database.models import Review, ReviewCategoryScore, User
from auth.auth import get_current_user

router = APIRouter()

class ReviewCategoryScoreRequest(BaseModel):
    category: str
    score: float

class ReviewRequest(BaseModel):
    freight_forwarder_id: str
    branch_id: Optional[str] = None
    overall_rating: float
    review_text: Optional[str] = None
    is_anonymous: bool = False
    category_scores: List[ReviewCategoryScoreRequest]

class ReviewResponse(BaseModel):
    id: str
    overall_rating: float
    review_text: Optional[str]
    is_anonymous: bool
    is_verified: bool
    created_at: str
    user: Optional[dict] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ReviewResponse])
async def get_reviews(
    freight_forwarder_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get reviews with optional freight forwarder filter"""
    query = db.query(Review).filter(Review.is_active == True)
    
    if freight_forwarder_id:
        query = query.filter(Review.freight_forwarder_id == freight_forwarder_id)
    
    reviews = query.offset(skip).limit(limit).all()
    
    review_responses = []
    for review in reviews:
        review_data = ReviewResponse.from_orm(review)
        if not review.is_anonymous:
            review_data.user = {
                "id": str(review.user.id),
                "username": review.user.username,
                "full_name": review.user.full_name,
                "avatar_url": review.user.avatar_url
            }
        review_responses.append(review_data)
    
    return review_responses

@router.post("/", response_model=ReviewResponse)
async def create_review(
    review_request: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new review"""
    # Validate overall rating
    if not 0 <= review_request.overall_rating <= 5:
        raise HTTPException(status_code=400, detail="Overall rating must be between 0 and 5")
    
    # Validate category scores
    for category_score in review_request.category_scores:
        if not 0 <= category_score.score <= 4:
            raise HTTPException(status_code=400, detail="Category scores must be between 0 and 4")
    
    # Create review
    review = Review(
        user_id=current_user.id,
        freight_forwarder_id=review_request.freight_forwarder_id,
        branch_id=review_request.branch_id,
        overall_rating=review_request.overall_rating,
        review_text=review_request.review_text,
        is_anonymous=review_request.is_anonymous
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Create category scores
    for category_score in review_request.category_scores:
        score = ReviewCategoryScore(
            review_id=review.id,
            category=category_score.category,
            score=category_score.score
        )
        db.add(score)
    
    db.commit()
    db.refresh(review)
    
    return ReviewResponse.from_orm(review)

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    db: Session = Depends(get_db)
):
    """Get specific review by ID"""
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.is_active == True
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review_data = ReviewResponse.from_orm(review)
    if not review.is_anonymous:
        review_data.user = {
            "id": str(review.user.id),
            "username": review.user.username,
            "full_name": review.user.full_name,
            "avatar_url": review.user.avatar_url
        }
    
    return review_data 