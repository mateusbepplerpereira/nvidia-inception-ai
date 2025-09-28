from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AgentTaskRequest(BaseModel):
    country: str = "Brazil"
    sector: Optional[str] = None
    limit: int = 10
    from_worker: bool = False
    job_id: Optional[int] = None
    search_strategy: str = "specific"

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

class TaskConfig(BaseModel):
    country: Optional[str] = None  # "Brazil", "America Latina", None para busca global
    sector: Optional[str] = None   # Setor específico ou None para busca por demanda
    limit: int = 10               # Limite de startups

class ScheduledJobCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str
    interval_value: int
    interval_unit: str  # "minutes", "hours", "days", "weeks", "months"
    task_config: TaskConfig

class ScheduledJobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    interval_value: Optional[int] = None
    interval_unit: Optional[str] = None
    task_config: Optional[TaskConfig] = None
    is_active: Optional[bool] = None

class ScheduledJobResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    task_type: str
    interval_value: int
    interval_unit: str
    task_config: Optional[Dict[str, Any]]
    is_active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    task_id: Optional[int]
    job_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

class TaskLogResponse(BaseModel):
    id: int
    task_name: str
    task_type: str
    status: str
    message: Optional[str]
    execution_time: Optional[float]
    scheduled_job_id: Optional[int]
    agent_task_id: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True