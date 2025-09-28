from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from database.connection import get_db
from database import models
from schemas.agent import AgentTaskRequest, AgentTaskResponse
from services.agent_service import AgentService
from services.task_manager import task_manager, process_orchestration_task

router = APIRouter()

@router.post("/task/run", response_model=AgentTaskResponse)
async def run_startup_pipeline(
    request: AgentTaskRequest,
    db: Session = Depends(get_db)
):
    """Rota unificada para orquestração completa: Discovery → Validation → Metrics"""
    service = AgentService(db)

    # Se a requisição vem do worker (job agendado), tratar de forma especial
    if request.from_worker and request.job_id:
        # Lógica separada para execução via worker (futuramente para e-mail)
        task_type_suffix = "_worker"
        message_prefix = "Worker job"
    else:
        # Execução manual normal
        task_type_suffix = ""
        message_prefix = "Manual"

    # Create task record
    task = service.create_task(
        task_type=f"orchestration{task_type_suffix}",
        agent_name="LangGraphOrchestrator",
        input_data=request.dict()
    )

    # Enqueue task for async processing
    task_manager.enqueue_task(
        task.id,
        process_orchestration_task,
        task.id,
        request.country,
        request.sector,
        getattr(request, 'limit', 5),
        request.from_worker,
        request.job_id,
        getattr(request, 'search_strategy', 'specific')
    )

    return AgentTaskResponse(
        task_id=task.id,
        status="pending",
        message=f"{message_prefix} orchestration pipeline queued (queue size: {task_manager.get_queue_size()})"
    )

# Rotas antigas removidas - agora tudo é feito via orquestração unificada

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/queue/status")
async def get_queue_status():
    """Retorna o status da fila de processamento"""
    return {
        "queue_size": task_manager.get_queue_size(),
        "worker_running": task_manager.is_worker_running(),
        "message": "Task queue operational" if task_manager.is_worker_running() else "Task queue stopped"
    }

@router.get("/metrics/ranking")
async def get_startup_ranking(
    limit: int = 200,  # Aumentar limite para incluir todas
    db: Session = Depends(get_db)
):
    """Retorna ranking de startups ordenadas por score total (inclui startups sem métricas)"""

    # Query para buscar TODAS as startups com LEFT JOIN para incluir as sem métricas
    all_startups = db.query(models.Startup, models.StartupMetrics)\
        .outerjoin(models.StartupMetrics, models.Startup.id == models.StartupMetrics.startup_id)\
        .order_by(
            models.StartupMetrics.total_score.desc().nullslast(),  # Métricas primeiro, nulls por último
            models.Startup.created_at.desc()  # Para startups sem métricas, ordenar por data
        )\
        .limit(limit)\
        .all()

    ranking = []
    for startup, metrics in all_startups:
        startup_data = {
            "rank": len(ranking) + 1,
            "startup": {
                "id": startup.id,
                "name": startup.name,
                "website": startup.website,
                "sector": startup.sector,
                "last_funding_amount": startup.last_funding_amount
            }
        }

        # Adicionar métricas se existirem
        if metrics:
            startup_data["metrics"] = {
                "market_demand_score": metrics.market_demand_score,
                "technical_level_score": metrics.technical_level_score,
                "partnership_potential_score": metrics.partnership_potential_score,
                "total_score": metrics.total_score,
                "analysis_date": metrics.analysis_date
            }
        else:
            # Startup sem métricas - retornar None para que o frontend saiba
            startup_data["metrics"] = None

        ranking.append(startup_data)

    # Estatísticas apenas das startups com métricas
    with_metrics = [r for r in ranking if r["metrics"] is not None]

    return {
        "ranking": ranking,
        "total_startups": len(ranking),
        "total_analyzed": len(with_metrics),
        "total_without_metrics": len(ranking) - len(with_metrics),
        "highest_score": with_metrics[0]["metrics"]["total_score"] if with_metrics else 0,
        "lowest_score": with_metrics[-1]["metrics"]["total_score"] if with_metrics else 0
    }

@router.get("/invalid/analysis")
async def get_invalid_startups_analysis(
    limit: int = 20,
    recommendation: str = None,
    db: Session = Depends(get_db)
):
    """Retorna análise detalhada de startups inválidas para investigação"""

    query = db.query(models.InvalidStartup)

    if recommendation:
        query = query.filter(models.InvalidStartup.recommendation == recommendation)

    invalid_startups = query.order_by(models.InvalidStartup.created_at.desc()).limit(limit).all()

    analysis = []
    for startup in invalid_startups:
        analysis.append({
            "id": startup.id,
            "name": startup.name,
            "website": startup.website,
            "sector": startup.sector,
            "reason": startup.reason,
            "validation_issues": startup.validation_issues,
            "validation_insight": startup.validation_insight,
            "confidence_level": startup.confidence_level,
            "recommendation": startup.recommendation,
            "full_validation_data": startup.full_validation_data,
            "created_at": startup.created_at
        })

    # Estatísticas agregadas
    total_invalid = db.query(models.InvalidStartup).count()
    by_recommendation = db.query(
        models.InvalidStartup.recommendation,
        func.count(models.InvalidStartup.id)
    ).group_by(models.InvalidStartup.recommendation).all()

    return {
        "invalid_startups": analysis,
        "total_invalid": total_invalid,
        "showing": len(analysis),
        "statistics": {
            "by_recommendation": dict(by_recommendation),
            "avg_confidence": db.query(func.avg(models.InvalidStartup.confidence_level)).scalar() or 0
        }
    }