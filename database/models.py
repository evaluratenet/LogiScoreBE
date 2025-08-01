from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    company_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # For email/password auth
    reset_token = Column(String(255), nullable=True)  # For password reset
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)  # For password reset
    verification_code = Column(String(6), nullable=True)  # For email verification
    verification_code_expires = Column(DateTime(timezone=True), nullable=True)  # For email verification
    user_type = Column(String(20), default='shipper')
    subscription_tier = Column(String(20), default='free')
    stripe_customer_id = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    reviews = relationship("Review", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")

class FreightForwarder(Base):
    __tablename__ = "freight_forwarders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)
    logo_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    branches = relationship("Branch", back_populates="freight_forwarder")
    reviews = relationship("Review", back_populates="freight_forwarder")

class Branch(Base):
    __tablename__ = "branches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    freight_forwarder_id = Column(UUID(as_uuid=True), ForeignKey("freight_forwarders.id"), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    freight_forwarder = relationship("FreightForwarder", back_populates="branches")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    freight_forwarder_id = Column(UUID(as_uuid=True), ForeignKey("freight_forwarders.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    overall_rating = Column(Float, nullable=False)
    review_text = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    freight_forwarder = relationship("FreightForwarder", back_populates="reviews")
    category_scores = relationship("ReviewCategoryScore", back_populates="review")

class ReviewCategoryScore(Base):
    __tablename__ = "review_category_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    category = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    review = relationship("Review", back_populates="category_scores")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reason = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='pending')
    admin_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AdCampaign(Base):
    __tablename__ = "ad_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    freight_forwarder_id = Column(UUID(as_uuid=True), ForeignKey("freight_forwarders.id"), nullable=False)
    campaign_name = Column(String(255), nullable=False)
    ad_type = Column(String(50), nullable=False)  # banner, spotlight, featured
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    budget = Column(Float, nullable=False)
    spent = Column(Float, default=0.0)
    status = Column(String(50), default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 