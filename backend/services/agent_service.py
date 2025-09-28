from sqlalchemy.orm import Session
from database import models
from typing import Dict, Any, Optional, List
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
        # Check if startup exists APENAS por nome (evitar falsos positivos por website)
        existing = None
        if startup_data.get("name"):
            existing = self.db.query(models.Startup).filter(
                models.Startup.name.ilike(startup_data.get("name"))
            ).first()

        # Preparar sources combinando dados existentes com validação
        sources = startup_data.get("sources", {})

        # Se há validação de sources, incluir metadata
        if startup_data.get("source_validation"):
            validation = startup_data["source_validation"]
            sources["validation_metadata"] = {
                "reliability_score": validation.get("reliability_score", 0),
                "is_reliable": validation.get("is_reliable", False),
                "funding_score": validation.get("funding_score", 0),
                "investor_score": validation.get("investor_score", 0),
                "validation_score": validation.get("validation_score", 0),
                "validated_at": datetime.now().isoformat(),
                "recommendation": validation.get("recommendation", "UNKNOWN")
            }

            if validation.get("issues"):
                sources["validation_metadata"]["issues"] = validation["issues"]

        if existing:
            # Update existing startup with new data
            print(f"Atualizando startup existente: {existing.name} (ID: {existing.id})")
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

            # Sempre atualizar sources com validação
            existing.sources = sources

            existing.has_venture_capital = bool(startup_data.get("investor_names"))
            existing.updated_at = datetime.now()

            self.db.commit()
            startup = existing
            print(f"Startup atualizada com sucesso: {existing.name}")
        else:
            # Create new startup
            print(f"Criando nova startup: {startup_data.get('name', 'N/A')}")
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
                sources=sources
            )
            self.db.add(startup)
            self.db.commit()
            self.db.refresh(startup)
            print(f"Nova startup criada: {startup.name} (ID: {startup.id})")

        print(f"==> RESULTADO: {startup.name} (ID: {startup.id}) - Setor: {startup.sector}")
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

    def get_valid_startups_for_context(self, country: str, sector: str = None) -> List[Dict]:
        """Busca startups válidas para contexto de exclusão"""
        query = self.db.query(models.Startup).filter(models.Startup.country == country)

        if sector:
            query = query.filter(models.Startup.sector == sector)

        startups = query.all()
        return [{"name": s.name, "website": s.website} for s in startups]

    def get_invalid_startups_for_context(self, country: str, sector: str = None) -> List[Dict]:
        """Busca startups inválidas para contexto de exclusão"""
        # Por enquanto retorna lista vazia, será implementado quando a tabela estiver criada
        return []

    def save_startup_metrics(self, startup_id: int, metrics_data: Dict) -> models.StartupMetrics:
        """Salva métricas de uma startup"""

        # Remove métricas antigas se existirem
        self.db.query(models.StartupMetrics).filter(
            models.StartupMetrics.startup_id == startup_id
        ).delete()

        metrics = models.StartupMetrics(
            startup_id=startup_id,
            market_demand_score=metrics_data.get("market_demand_score", 0),
            technical_level_score=metrics_data.get("technical_level_score", 0),
            partnership_potential_score=metrics_data.get("partnership_potential_score", 0),
            total_score=metrics_data.get("total_score", 0)
        )

        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)
        return metrics

    def save_invalid_startup(self, invalid_data: Dict) -> models.InvalidStartup:
        """Salva startup inválida com insights detalhados"""
        invalid_startup = models.InvalidStartup(
            name=invalid_data.get("name"),
            website=invalid_data.get("website"),
            sector=invalid_data.get("sector"),
            reason=invalid_data.get("reason"),
            validation_issues=invalid_data.get("issues", []),
            validation_insight=invalid_data.get("validation_insight"),
            confidence_level=invalid_data.get("confidence_level", 0.0),
            recommendation=invalid_data.get("recommendation"),
            full_validation_data=invalid_data.get("full_validation_data", {})
        )

        self.db.add(invalid_startup)
        self.db.commit()
        self.db.refresh(invalid_startup)
        return invalid_startup