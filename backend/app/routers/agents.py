from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from database.connection import get_db
from database import models
from agents.startup_crew import StartupDiscoveryCrew
from agents.validation_agent import StartupValidationAgent
from schemas.agent import AgentTaskRequest, AgentTaskResponse
from services.agent_service import AgentService
from services.task_manager import task_manager, process_discovery_task

router = APIRouter()

@router.post("/discover", response_model=AgentTaskResponse)
async def discover_startups(
    request: AgentTaskRequest,
    db: Session = Depends(get_db)
):
    service = AgentService(db)

    # Create task record
    task = service.create_task(
        task_type="discovery",
        agent_name="StartupDiscoveryCrew",
        input_data=request.dict()
    )

    # Enqueue task for async processing
    task_manager.enqueue_task(
        task.id,
        process_discovery_task,
        task.id,
        request.country,
        request.sector
    )

    return AgentTaskResponse(
        task_id=task.id,
        status="pending",
        message=f"Discovery task queued (queue size: {task_manager.get_queue_size()})"
    )

@router.post("/analyze/{startup_id}")
async def analyze_startup(
    startup_id: int,
    db: Session = Depends(get_db)
):
    service = AgentService(db)
    crew = StartupDiscoveryCrew()

    # Get startup data
    startup = db.query(models.Startup).filter(models.Startup.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    # Run analysis
    startup_data = {
        "name": startup.name,
        "website": startup.website,
        "sector": startup.sector,
        "ai_technologies": startup.ai_technologies,
        "funding": startup.last_funding_amount
    }

    result = crew.analyze_single_startup(startup_data)

    # Save analysis
    service.save_analysis(startup_id, result)

    return result

@router.post("/batch-discover")
async def batch_discover_startups(
    countries: List[str] = ["Brazil", "Argentina", "Mexico"],
    db: Session = Depends(get_db)
):
    """Discover startups from multiple countries"""
    service = AgentService(db)
    tasks = []

    for country in countries:
        task = service.create_task(
            task_type="discovery",
            agent_name="StartupDiscoveryCrew",
            input_data={"country": country, "limit": 5}
        )
        tasks.append(task)

        # Enqueue each country discovery
        task_manager.enqueue_task(
            task.id,
            process_discovery_task,
            task.id,
            country,
            None
        )

    return {
        "message": f"Started discovery for {len(countries)} countries",
        "task_ids": [t.id for t in tasks],
        "queue_size": task_manager.get_queue_size()
    }

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

@router.post("/validate/{startup_id}")
async def validate_startup(startup_id: int, db: Session = Depends(get_db)):
    """Valida as informações de uma startup específica"""
    startup = db.query(models.Startup).filter(models.Startup.id == startup_id).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    # Converte startup para dict
    startup_data = {
        "name": startup.name,
        "website": str(startup.website) if startup.website else None,
        "sector": startup.sector,
        "founded_year": startup.founded_year,
        "country": startup.country,
        "city": startup.city,
        "description": startup.description,
        "ai_technologies": startup.ai_technologies,
        "last_funding_amount": startup.last_funding_amount,
        "investor_names": startup.investor_names,
        "ceo_name": startup.ceo_name,
        "ceo_linkedin": startup.ceo_linkedin,
        "cto_name": startup.cto_name,
        "cto_linkedin": startup.cto_linkedin,
        "has_venture_capital": startup.has_venture_capital
    }

    validator = StartupValidationAgent()
    validation_result = validator.validate_startup_info(startup_data)

    return {
        "startup_id": startup_id,
        "startup_name": startup.name,
        "validation": validation_result
    }

@router.post("/validate-batch")
async def validate_batch_startups(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Valida um lote de startups"""
    startups = db.query(models.Startup).limit(limit).all()

    if not startups:
        raise HTTPException(status_code=404, detail="No startups found")

    startups_data = []
    for startup in startups:
        startup_data = {
            "id": startup.id,
            "name": startup.name,
            "website": str(startup.website) if startup.website else None,
            "sector": startup.sector,
            "founded_year": startup.founded_year,
            "country": startup.country,
            "city": startup.city,
            "description": startup.description,
            "ai_technologies": startup.ai_technologies,
            "last_funding_amount": startup.last_funding_amount,
            "investor_names": startup.investor_names,
            "ceo_name": startup.ceo_name,
            "ceo_linkedin": startup.ceo_linkedin,
            "cto_name": startup.cto_name,
            "cto_linkedin": startup.cto_linkedin,
            "has_venture_capital": startup.has_venture_capital
        }
        startups_data.append(startup_data)

    validator = StartupValidationAgent()
    validation_results = validator.batch_validate_startups(startups_data)

    return validation_results

# Task processing is now handled by TaskManager in services/task_manager.py