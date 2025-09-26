from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class StartupBase(BaseModel):
    name: str
    website: Optional[Union[HttpUrl, str]] = None
    sector: Optional[str] = None
    founded_year: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    ai_technologies: Optional[List[str]] = []
    last_funding_amount: Optional[float] = None
    last_funding_date: Optional[datetime] = None
    total_funding: Optional[float] = None
    investor_names: Optional[List[str]] = []
    has_venture_capital: bool = False
    sources: Optional[Dict[str, Any]] = {}

    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        if v is None or v == "" or v in ["Não encontrado", "N/A", "Not found"]:
            return None
        try:
            return HttpUrl(v) if isinstance(v, str) else v
        except:
            return None

class StartupCreate(StartupBase):
    pass

class StartupUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[Union[HttpUrl, str]] = None
    sector: Optional[str] = None
    founded_year: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    ai_technologies: Optional[List[str]] = None
    last_funding_amount: Optional[float] = None
    last_funding_date: Optional[datetime] = None
    total_funding: Optional[float] = None
    investor_names: Optional[List[str]] = None
    has_venture_capital: Optional[bool] = None
    sources: Optional[Dict[str, Any]] = None

    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        if v is None or v == "" or v in ["Não encontrado", "N/A", "Not found"]:
            return None
        try:
            return HttpUrl(v) if isinstance(v, str) else v
        except:
            return None

class LeadershipInfo(BaseModel):
    name: str
    role: str
    profile_url: Optional[str] = None  # GitHub, personal site, or company page
    email: Optional[str] = None

class StartupAnalysis(BaseModel):
    priority_score: float
    technology_score: float
    market_opportunity_score: float
    team_score: float
    insights: Dict[str, Any]
    recommendation: str
    analysis_date: datetime

class StartupResponse(StartupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    leadership: Optional[List[LeadershipInfo]] = []

    class Config:
        from_attributes = True

class ReportFilters(BaseModel):
    sectors: Optional[List[str]] = []
    technologies: Optional[List[str]] = []
    max_startups: int = 50