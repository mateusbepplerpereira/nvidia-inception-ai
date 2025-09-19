from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database import models
from schemas.startup import StartupCreate, StartupResponse, StartupUpdate
from services.startup_service import StartupService

router = APIRouter()

@router.get("/", response_model=List[StartupResponse])
async def list_startups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country: Optional[str] = None,
    sector: Optional[str] = None,
    has_vc: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    service = StartupService(db)
    return service.get_startups(skip, limit, country, sector, has_vc)

@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(startup_id: int, db: Session = Depends(get_db)):
    service = StartupService(db)
    startup = service.get_startup_by_id(startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@router.post("/", response_model=StartupResponse)
async def create_startup(startup: StartupCreate, db: Session = Depends(get_db)):
    service = StartupService(db)
    return service.create_startup(startup)

@router.put("/{startup_id}", response_model=StartupResponse)
async def update_startup(
    startup_id: int,
    startup: StartupUpdate,
    db: Session = Depends(get_db)
):
    service = StartupService(db)
    updated = service.update_startup(startup_id, startup)
    if not updated:
        raise HTTPException(status_code=404, detail="Startup not found")
    return updated

@router.delete("/{startup_id}")
async def delete_startup(startup_id: int, db: Session = Depends(get_db)):
    service = StartupService(db)
    if not service.delete_startup(startup_id):
        raise HTTPException(status_code=404, detail="Startup not found")
    return {"message": "Startup deleted successfully"}

# Analysis functionality removed