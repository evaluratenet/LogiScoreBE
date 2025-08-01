from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta, datetime
import os
import uuid
from passlib.context import CryptContext

from database.database import get_db
from database.models import User
from auth.auth import (
    get_current_user, 
    create_access_token, 
    authenticate_github_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

class GitHubAuthRequest(BaseModel):
    code: str

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    company: Optional[str] = None
    user_type: Optional[str] = "shipper"

class SigninRequest(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    reset_token: str
    new_password: str

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
        
    @classmethod
    def from_orm(cls, obj):
        # Convert UUID to string for the id field
        data = {
            'id': str(obj.id),
            'email': obj.email,
            'username': obj.username,
            'full_name': obj.full_name,
            'avatar_url': obj.avatar_url,
            'company_name': obj.company_name,
            'user_type': obj.user_type,
            'subscription_tier': obj.subscription_tier,
            'is_verified': obj.is_verified,
            'is_active': obj.is_active
        }
        return cls(**data)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.get("/github/auth")
async def get_github_auth_url():
    """Get GitHub OAuth authorization URL"""
    github_client_id = os.getenv("GITHUB_CLIENT_ID")
    if not github_client_id:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    
    # Redirect URL should be your frontend callback URL
    redirect_uri = "https://logiscore-frontend.vercel.app/callback"
    auth_url = f"https://github.com/login/oauth/authorize?client_id={github_client_id}&redirect_uri={redirect_uri}&scope=user:email"
    
    return {"auth_url": auth_url}

@router.post("/github/callback", response_model=TokenResponse)
async def github_callback(
    auth_request: GitHubAuthRequest,
    db: Session = Depends(get_db)
):
    """Handle GitHub OAuth callback"""
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

@router.post("/signup", response_model=TokenResponse)
async def signup(
    signup_request: SignupRequest,
    db: Session = Depends(get_db)
):
    """Register a new user with email/password"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == signup_request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        hashed_password = pwd_context.hash(signup_request.password)
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            email=signup_request.email,
            username=signup_request.name,
            full_name=signup_request.name,
            company_name=signup_request.company,
            hashed_password=hashed_password,
            user_type=signup_request.user_type,
            subscription_tier="free",
            is_verified=False,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
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
        import logging
        logging.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@router.post("/signin", response_model=TokenResponse)
async def signin(
    signin_request: SigninRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with email/password"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == signin_request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not pwd_context.verify(signin_request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
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
        import logging
        logging.error(f"Signin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signin failed: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    change_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not pwd_context.verify(change_request.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = pwd_context.hash(change_request.new_password)
        
        # Update password in database
        current_user.hashed_password = new_hashed_password
        db.commit()
        
        return {"message": "Password changed successfully"}
    except Exception as e:
        import logging
        logging.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.post("/forgot-password")
async def forgot_password(
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Send password reset email"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == forgot_request.email).first()
        if not user:
            # Don't reveal if user exists or not for security
            return {"message": "If the email exists, a reset link has been sent"}
        
        # Generate reset token (simple implementation - in production, use proper email service)
        reset_token = str(uuid.uuid4())
        
        # Store reset token in user record (you might want a separate table for this)
        # For now, we'll use a simple approach
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # In production, send email here
        # For now, just return the token (in production, send via email)
        return {
            "message": "Password reset link sent to email",
            "reset_token": reset_token,  # Remove this in production
            "expires_in": "1 hour"
        }
    except Exception as e:
        import logging
        logging.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}"
        )

@router.post("/reset-password")
async def reset_password(
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == reset_request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or reset token"
            )
        
        # Verify reset token
        if not user.reset_token or user.reset_token != reset_request.reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Check if token is expired
        if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Hash new password
        new_hashed_password = pwd_context.hash(reset_request.new_password)
        
        # Update password and clear reset token
        user.hashed_password = new_hashed_password
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        
        return {"message": "Password reset successfully"}
    except Exception as e:
        import logging
        logging.error(f"Reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        ) 