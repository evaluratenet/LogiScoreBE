from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import stripe
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional
import logging

# Import our modules
from database.database import get_db, get_engine
from database.models import Base
from auth.auth import get_current_user, create_access_token
from routes import users, freight_forwarders, reviews, search

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LogiScore API",
    description="Freight forwarder review and rating platform API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://logiscore.net",
        "https://logiscore-frontend.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Create database tables (only if database is available)
try:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables: {e}")

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(freight_forwarders.router, prefix="/api/freight-forwarders", tags=["freight-forwarders"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(search.router, prefix="/api/search", tags=["search"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "LogiScore API is running",
        "version": "1.0.2",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for development"""
    return {"message": "API is working correctly"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 