from sqlalchemy.orm import Session
from typing import List, Optional
from database import models
from schemas.startup import StartupCreate, StartupUpdate

class StartupService:
    def __init__(self, db: Session):
        self.db = db

    def get_startups(
        self,
        skip: int = 0,
        limit: int = 100,
        country: Optional[str] = None,
        sector: Optional[str] = None,
        has_vc: Optional[bool] = None
    ) -> List[models.Startup]:
        query = self.db.query(models.Startup)

        if country:
            query = query.filter(models.Startup.country == country)
        if sector:
            query = query.filter(models.Startup.sector == sector)
        if has_vc is not None:
            query = query.filter(models.Startup.has_venture_capital == has_vc)

        return query.offset(skip).limit(limit).all()

    def get_startup_by_id(self, startup_id: int) -> Optional[models.Startup]:
        return self.db.query(models.Startup).filter(models.Startup.id == startup_id).first()

    def create_startup(self, startup: StartupCreate) -> models.Startup:
        db_startup = models.Startup(**startup.dict())
        self.db.add(db_startup)
        self.db.commit()
        self.db.refresh(db_startup)
        return db_startup

    def update_startup(self, startup_id: int, startup: StartupUpdate) -> Optional[models.Startup]:
        db_startup = self.get_startup_by_id(startup_id)
        if not db_startup:
            return None

        update_data = startup.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_startup, field, value)

        self.db.commit()
        self.db.refresh(db_startup)
        return db_startup

    def delete_startup(self, startup_id: int) -> bool:
        db_startup = self.get_startup_by_id(startup_id)
        if not db_startup:
            return False

        self.db.delete(db_startup)
        self.db.commit()
        return True

    # Analysis functionality removed