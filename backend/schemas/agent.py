from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AgentTaskRequest(BaseModel):
    country: str = "Brazil"
    sector: Optional[str] = None
    limit: int = 10

class AgentTaskResponse(BaseModel):
    task_id: int
    status: str
    message: str
    result: Optional[Dict[str, Any]] = None

class AgentTaskStatus(BaseModel):
    id: int
    task_type: str
    status: str
    agent_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True