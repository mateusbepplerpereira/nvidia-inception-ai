from sqlalchemy.orm import Session
from database import models
from typing import Dict, Any, Optional
from datetime import datetime

class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_type: str, agent_name: str, input_data: Dict) -> models.AgentTask:
        task = models.AgentTask(
            task_type=task_type,
            agent_name=agent_name,
            input_data=input_data,
            status="pending",
            started_at=datetime.now()
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_task(
        self,
        task_id: int,
        status: str,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        task = self.db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()
        if task:
            task.status = status
            if output_data:
                task.output_data = output_data
            if error_message:
                task.error_message = error_message
            if status in ["completed", "failed"]:
                task.completed_at = datetime.now()
            self.db.commit()

    def get_task(self, task_id: int) -> Optional[models.AgentTask]:
        return self.db.query(models.AgentTask).filter(models.AgentTask.id == task_id).first()

    def save_startup_from_discovery(self, startup_data: Dict):
        # Check if startup exists by name or website
        existing = self.db.query(models.Startup).filter(
            (models.Startup.name == startup_data.get("name")) |
            (models.Startup.website == startup_data.get("website"))
        ).first()

        if existing:
            # Update existing startup with new data
            if startup_data.get("website"):
                existing.website = startup_data.get("website")
            if startup_data.get("sector"):
                existing.sector = startup_data.get("sector")
            if startup_data.get("founded_year"):
                existing.founded_year = startup_data.get("founded_year")
            if startup_data.get("country"):
                existing.country = startup_data.get("country")
            if startup_data.get("city"):
                existing.city = startup_data.get("city")
            if startup_data.get("description"):
                existing.description = startup_data.get("description")
            if startup_data.get("ai_technologies"):
                existing.ai_technologies = startup_data.get("ai_technologies")
            if startup_data.get("last_funding_amount"):
                existing.last_funding_amount = startup_data.get("last_funding_amount")
            if startup_data.get("investor_names"):
                existing.investor_names = startup_data.get("investor_names")
            if startup_data.get("ceo_name"):
                existing.ceo_name = startup_data.get("ceo_name")
            if startup_data.get("ceo_linkedin"):
                existing.ceo_linkedin = startup_data.get("ceo_linkedin")
            if startup_data.get("cto_name"):
                existing.cto_name = startup_data.get("cto_name")
            if startup_data.get("cto_linkedin"):
                existing.cto_linkedin = startup_data.get("cto_linkedin")

            existing.has_venture_capital = bool(startup_data.get("investor_names"))
            existing.updated_at = datetime.now()

            self.db.commit()
            startup = existing
        else:
            # Create new startup
            startup = models.Startup(
                name=startup_data.get("name"),
                website=startup_data.get("website"),
                sector=startup_data.get("sector"),
                founded_year=startup_data.get("founded_year"),
                country=startup_data.get("country", "Brazil"),
                city=startup_data.get("city"),
                description=startup_data.get("description"),
                ai_technologies=startup_data.get("ai_technologies", []),
                last_funding_amount=startup_data.get("last_funding_amount"),
                investor_names=startup_data.get("investor_names", []),
                has_venture_capital=bool(startup_data.get("investor_names")),
                ceo_name=startup_data.get("ceo_name"),
                ceo_linkedin=startup_data.get("ceo_linkedin"),
                cto_name=startup_data.get("cto_name"),
                cto_linkedin=startup_data.get("cto_linkedin")
            )
            self.db.add(startup)
            self.db.commit()
            self.db.refresh(startup)

        return startup

    def save_analysis(self, startup_id: int, analysis_data: Dict):
        analysis = models.Analysis(
            startup_id=startup_id,
            priority_score=analysis_data.get("priority_score", 0),
            technology_score=analysis_data.get("technology_score", 0),
            market_opportunity_score=analysis_data.get("market_opportunity_score", 0),
            team_score=analysis_data.get("team_score", 0),
            insights=analysis_data.get("insights", {}),
            recommendation=analysis_data.get("recommendation", "")
        )
        self.db.add(analysis)
        self.db.commit()
        return analysis