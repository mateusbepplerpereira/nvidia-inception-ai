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
    ceo_name = Column(String(255))
    ceo_linkedin = Column(String(500))
    cto_name = Column(String(255))
    cto_linkedin = Column(String(500))
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
    ceo_name = Column(String(255))
    cto_name = Column(String(255))
    ceo_linkedin = Column(String(500))
    cto_linkedin = Column(String(500))
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
    technical_level_score = Column(Float)  # 0-100: Nível técnico dos CTOs
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