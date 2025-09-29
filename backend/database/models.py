from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class Startup(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    website = Column(String(500))
    sector = Column(String(255))
    founded_year = Column(Integer)
    country = Column(String(100))
    city = Column(String(100))
    description = Column(Text)
    ai_technologies = Column(JSON)  # ["Computer Vision", "NLP", "Robotics"]
    last_funding_amount = Column(Float)
    last_funding_date = Column(DateTime)
    total_funding = Column(Float)
    investor_names = Column(JSON)  # ["Investor 1", "Investor 2"]
    has_venture_capital = Column(Boolean, default=False)
    sources = Column(JSON)  # {"funding": ["Crunchbase", "PitchBook"], "investors": ["AngelList"], "validation": ["company_website"]}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    leadership = relationship("Leadership", back_populates="startup", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="startup", cascade="all, delete-orphan")
    metrics = relationship("StartupMetrics", back_populates="startup", cascade="all, delete-orphan")

class Leadership(Base):
    __tablename__ = "leadership"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    name = Column(String(255))
    role = Column(String(100))  # CTO, Tech Lead, etc
    profile_url = Column(String(500))  # GitHub, personal site, or company page
    email = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    startup = relationship("Startup", back_populates="leadership")

class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))
    priority_score = Column(Float)  # 0-100
    technology_score = Column(Float)
    market_opportunity_score = Column(Float)
    team_score = Column(Float)
    insights = Column(JSON)  # Structured insights from AI analysis
    recommendation = Column(Text)
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())

    startup = relationship("Startup", back_populates="analysis")

class InvalidStartup(Base):
    __tablename__ = "invalid_startups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500))
    sector = Column(String(255))
    reason = Column(Text)  # Motivo da invalidação
    validation_issues = Column(JSON)  # Issues específicos encontrados
    validation_insight = Column(Text)  # Insight detalhado da IA sobre a invalidação
    confidence_level = Column(Float)  # Nível de confiança da invalidação (0-1)
    recommendation = Column(String(100))  # REJECT/INVESTIGATE/MANUAL_REVIEW
    full_validation_data = Column(JSON)  # Dados completos da validação
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StartupMetrics(Base):
    __tablename__ = "startup_metrics"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"))

    # Métricas principais
    market_demand_score = Column(Float)  # 0-100: Alta demanda do mercado
    technical_level_score = Column(Float)  # 0-100: Nível técnico da solução
    partnership_potential_score = Column(Float)  # 0-100: Potencial de parceria

    # Score total
    total_score = Column(Float)  # Média ponderada das métricas

    # Metadados
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    analysis_version = Column(String(50), default="1.0")

    startup = relationship("Startup", back_populates="metrics")

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(100))  # "orchestration", "discovery", "validation", "metrics"
    status = Column(String(50))  # "pending", "running", "completed", "failed"
    agent_name = Column(String(100))
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(String(100), nullable=False)  # "startup_discovery", "newsletter"
    interval_value = Column(Integer, nullable=False)  # número
    interval_unit = Column(String(20), nullable=False)  # "minutes", "hours", "days", "weeks", "months"

    # Parâmetros configuráveis da task
    task_config = Column(JSON)  # {"country": "Brazil", "sector": "FinTech", "limit": 10, "search_strategy": "specific"}

    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    task_logs = relationship("TaskLog", back_populates="scheduled_job")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # "success", "error", "info", "warning"
    is_read = Column(Boolean, default=False)
    task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # "started", "completed", "failed"
    message = Column(Text)
    execution_time = Column(Float)  # em segundos
    scheduled_job_id = Column(Integer, ForeignKey("scheduled_jobs.id"), nullable=True)
    agent_task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scheduled_job = relationship("ScheduledJob", back_populates="task_logs")

class NewsletterEmail(Base):
    __tablename__ = "newsletter_emails"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class NewsletterSent(Base):
    __tablename__ = "newsletter_sent"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id", ondelete="CASCADE"))
    email = Column(String(255), nullable=False)
    report_data = Column(JSON)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    scheduled_job = relationship("ScheduledJob")