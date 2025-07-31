from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from database.database import get_db
from database.models import User
from auth.auth import (
    get_current_user, 
    create_access_token, 
    authenticate_github_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

class GitHubAuthRequest(BaseModel):
    code: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    company_name: Optional[str]
    user_type: str
    subscription_tier: str
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/auth/github", response_model=TokenResponse)
async def github_auth(
    auth_request: GitHubAuthRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with GitHub OAuth"""
    try:
        user = await authenticate_github_user(auth_request.code, db)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user) 