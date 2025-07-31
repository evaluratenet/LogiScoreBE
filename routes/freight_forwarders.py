from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database.database import get_db
from database.models import FreightForwarder, Branch

router = APIRouter()

class FreightForwarderResponse(BaseModel):
    id: str
    name: str
    website: Optional[str]
    logo_url: Optional[str]
    description: Optional[str]
    headquarters: Optional[str]
    founded_year: Optional[int]
    employee_count: Optional[str]
    services: Optional[str]
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True

class BranchResponse(BaseModel):
    id: str
    name: str
    location: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[FreightForwarderResponse])
async def get_freight_forwarders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get list of freight forwarders with optional search"""
    query = db.query(FreightForwarder).filter(FreightForwarder.is_active == True)
    
    if search:
        query = query.filter(
            FreightForwarder.name.ilike(f"%{search}%") |
            FreightForwarder.description.ilike(f"%{search}%") |
            FreightForwarder.headquarters.ilike(f"%{search}%")
        )
    
    freight_forwarders = query.offset(skip).limit(limit).all()
    return [FreightForwarderResponse.from_orm(ff) for ff in freight_forwarders]

@router.get("/{freight_forwarder_id}", response_model=FreightForwarderResponse)
async def get_freight_forwarder(
    freight_forwarder_id: str,
    db: Session = Depends(get_db)
):
    """Get specific freight forwarder by ID"""
    freight_forwarder = db.query(FreightForwarder).filter(
        FreightForwarder.id == freight_forwarder_id,
        FreightForwarder.is_active == True
    ).first()
    
    if not freight_forwarder:
        raise HTTPException(status_code=404, detail="Freight forwarder not found")
    
    return FreightForwarderResponse.from_orm(freight_forwarder)

@router.get("/{freight_forwarder_id}/branches", response_model=List[BranchResponse])
async def get_freight_forwarder_branches(
    freight_forwarder_id: str,
    db: Session = Depends(get_db)
):
    """Get branches for a specific freight forwarder"""
    branches = db.query(Branch).filter(
        Branch.freight_forwarder_id == freight_forwarder_id,
        Branch.is_active == True
    ).all()
    
    return [BranchResponse.from_orm(branch) for branch in branches] 