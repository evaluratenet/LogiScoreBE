from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from database.database import get_db
from database.models import User, FreightForwarder, Review, Dispute, Branch
from auth.auth import get_current_user

router = APIRouter()

# Pydantic models for admin responses
class DashboardStats(BaseModel):
    total_users: int
    total_companies: int
    total_reviews: int
    pending_disputes: int
    pending_reviews: int
    total_revenue: float

class AdminUser(BaseModel):
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    company_name: Optional[str]
    user_type: str
    subscription_tier: str
    is_verified: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True

class AdminReview(BaseModel):
    id: str
    freight_forwarder_name: str
    branch_name: Optional[str]
    reviewer_name: str
    rating: int
    comment: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True

class AdminDispute(BaseModel):
    id: str
    freight_forwarder_name: str
    issue: str
    status: str
    created_at: str

    class Config:
        from_attributes = True

class AdminCompany(BaseModel):
    id: str
    name: str
    website: Optional[str]
    logo_url: Optional[str]
    branches_count: int
    reviews_count: int
    status: str

    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    user_id: str
    tier: str
    comment: str
    duration: int
    is_paid: bool

class CompanyCreate(BaseModel):
    name: str
    website: Optional[str] = None
    description: Optional[str] = None
    headquarters_country: Optional[str] = None

# Helper function to check if user is admin
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    try:
        # Count total users
        total_users = db.query(User).count()
        
        # Count total companies
        total_companies = db.query(FreightForwarder).count()
        
        # Count total reviews
        total_reviews = db.query(Review).count()
        
        # Count pending disputes
        pending_disputes = db.query(Dispute).filter(Dispute.status == "open").count()
        
        # Count pending reviews (reviews that need moderation)
        pending_reviews = db.query(Review).filter(Review.status == "pending").count()
        
        # Calculate revenue (mock calculation for now)
        # In a real app, this would come from subscription payments
        total_revenue = 45600.0  # Mock value
        
        return DashboardStats(
            total_users=total_users,
            total_companies=total_companies,
            total_reviews=total_reviews,
            pending_disputes=pending_disputes,
            pending_reviews=pending_reviews,
            total_revenue=total_revenue
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )

@router.get("/users", response_model=List[AdminUser])
async def get_users(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get all users with filtering and pagination"""
    try:
        query = db.query(User)
        
        if search:
            query = query.filter(
                User.email.contains(search) | 
                User.username.contains(search) |
                User.full_name.contains(search)
            )
        
        if user_type:
            query = query.filter(User.user_type == user_type)
        
        users = query.offset(skip).limit(limit).all()
        
        return [
            AdminUser(
                id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                company_name=user.company_name,
                user_type=user.user_type,
                subscription_tier=user.subscription_tier,
                is_verified=user.is_verified,
                is_active=user.is_active,
                created_at=user.created_at.isoformat() if user.created_at else None
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )

@router.put("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    subscription_update: SubscriptionUpdate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user subscription"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update subscription tier
        user.subscription_tier = subscription_update.tier
        
        # In a real app, you would also update subscription details in a separate table
        # For now, we'll just update the tier
        
        db.commit()
        
        return {"message": "Subscription updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )

@router.get("/reviews", response_model=List[AdminReview])
async def get_reviews(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get reviews for admin moderation"""
    try:
        query = db.query(Review).join(FreightForwarder)
        
        if status_filter:
            query = query.filter(Review.status == status_filter)
        
        reviews = query.offset(skip).limit(limit).all()
        
        return [
            AdminReview(
                id=str(review.id),
                freight_forwarder_name=review.freight_forwarder.name,
                branch_name=review.branch.name if review.branch else None,
                reviewer_name=review.user.username or "Anonymous",
                rating=review.rating,
                comment=review.comment,
                status=review.status,
                created_at=review.created_at.isoformat() if review.created_at else None
            )
            for review in reviews
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reviews: {str(e)}"
        )

@router.put("/reviews/{review_id}/approve")
async def approve_review(
    review_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Approve a review"""
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        review.status = "approved"
        db.commit()
        
        return {"message": "Review approved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve review: {str(e)}"
        )

@router.put("/reviews/{review_id}/reject")
async def reject_review(
    review_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reject a review"""
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        review.status = "rejected"
        db.commit()
        
        return {"message": "Review rejected successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject review: {str(e)}"
        )

@router.get("/disputes", response_model=List[AdminDispute])
async def get_disputes(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get disputes for admin resolution"""
    try:
        query = db.query(Dispute).join(FreightForwarder)
        
        if status_filter:
            query = query.filter(Dispute.status == status_filter)
        
        disputes = query.offset(skip).limit(limit).all()
        
        return [
            AdminDispute(
                id=str(dispute.id),
                freight_forwarder_name=dispute.freight_forwarder.name,
                issue=dispute.issue,
                status=dispute.status,
                created_at=dispute.created_at.isoformat() if dispute.created_at else None
            )
            for dispute in disputes
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get disputes: {str(e)}"
        )

@router.put("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Resolve a dispute"""
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispute not found"
            )
        
        dispute.status = "resolved"
        db.commit()
        
        return {"message": "Dispute resolved successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve dispute: {str(e)}"
        )

@router.get("/companies", response_model=List[AdminCompany])
async def get_companies(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """Get all companies with stats"""
    try:
        query = db.query(FreightForwarder)
        
        if search:
            query = query.filter(FreightForwarder.name.contains(search))
        
        companies = query.offset(skip).limit(limit).all()
        
        result = []
        for company in companies:
            # Count branches
            branches_count = db.query(Branch).filter(Branch.freight_forwarder_id == company.id).count()
            
            # Count reviews
            reviews_count = db.query(Review).filter(Review.freight_forwarder_id == company.id).count()
            
            result.append(AdminCompany(
                id=str(company.id),
                name=company.name,
                website=company.website,
                logo_url=company.logo_url,
                branches_count=branches_count,
                reviews_count=reviews_count,
                status="active" if company.is_active else "inactive"
            ))
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get companies: {str(e)}"
        )

@router.post("/companies", response_model=AdminCompany)
async def create_company(
    company_data: CompanyCreate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new company"""
    try:
        # Check if company already exists
        existing_company = db.query(FreightForwarder).filter(
            FreightForwarder.name == company_data.name
        ).first()
        
        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this name already exists"
            )
        
        new_company = FreightForwarder(
            id=str(uuid.uuid4()),
            name=company_data.name,
            website=company_data.website,
            description=company_data.description,
            headquarters_country=company_data.headquarters_country,
            is_active=True
        )
        
        db.add(new_company)
        db.commit()
        db.refresh(new_company)
        
        return AdminCompany(
            id=str(new_company.id),
            name=new_company.name,
            website=new_company.website,
            logo_url=new_company.logo_url,
            branches_count=0,
            reviews_count=0,
            status="active"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company: {str(e)}"
        ) 