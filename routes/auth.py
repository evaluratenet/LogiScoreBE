from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from database.database import get_db
from database.models import User
from auth.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

class EmailAuthRequest(BaseModel):
    email: str

class CodeVerificationRequest(BaseModel):
    email: str
    code: str

class EmailAuthResponse(BaseModel):
    message: str
    expires_in: int

class CodeVerificationResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@logiscore.com")

def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email: str, code: str, expires_in: int) -> bool:
    """Send verification code email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = "LogiScore Verification Code"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>LogiScore Verification Code</h2>
            <p>Your verification code is: <strong>{code}</strong></p>
            <p>This code will expire in {expires_in} minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The LogiScore Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        if SMTP_USERNAME and SMTP_PASSWORD:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        else:
            # For development/testing, just print the code
            print(f"Verification code for {email}: {code}")
            return True
            
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@router.post("/send-code", response_model=EmailAuthResponse)
async def send_verification_code(
    request: EmailAuthRequest,
    db: Session = Depends(get_db)
):
    """Send verification code to user's email"""
    try:
        email = request.email.lower().strip()
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        # Generate verification code
        code = generate_verification_code()
        expires_in = 10  # 10 minutes
        
        # Store code in user record (or create user if doesn't exist)
        if user:
            # Update existing user
            user.verification_code = code
            user.verification_code_expires = datetime.utcnow() + timedelta(minutes=expires_in)
        else:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=email.split('@')[0],  # Use email prefix as username
                user_type="shipper",  # Default user type
                subscription_tier="free",
                is_verified=False,
                is_active=True,
                verification_code=code,
                verification_code_expires=datetime.utcnow() + timedelta(minutes=expires_in)
            )
            db.add(user)
        
        db.commit()
        
        # Send verification email
        if send_verification_email(email, code, expires_in):
            return EmailAuthResponse(
                message="Verification code sent to your email",
                expires_in=expires_in
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification code: {str(e)}"
        )

@router.post("/verify-code", response_model=CodeVerificationResponse)
async def verify_code(
    request: CodeVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify the code and authenticate user"""
    try:
        email = request.email.lower().strip()
        code = request.code.strip()
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if code is valid and not expired
        if not user.verification_code or user.verification_code != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        if not user.verification_code_expires or user.verification_code_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired"
            )
        
        # Clear verification code
        user.verification_code = None
        user.verification_code_expires = None
        user.is_verified = True
        db.commit()
        
        # Generate access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        # Return user data
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "avatar_url": user.avatar_url,
            "company_name": user.company_name,
            "user_type": user.user_type,
            "subscription_tier": user.subscription_tier,
            "is_verified": user.is_verified,
            "is_active": user.is_active
        }
        
        return CodeVerificationResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify code: {str(e)}"
        ) 