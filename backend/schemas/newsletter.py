from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class NewsletterEmailCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class NewsletterEmailUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class NewsletterEmailResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class NewsletterSentResponse(BaseModel):
    id: int
    job_id: int
    email: str
    report_data: dict
    sent_at: datetime

    class Config:
        from_attributes = True