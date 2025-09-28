from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from database.models import ScheduledJob
from schemas.agent import ScheduledJobCreate, ScheduledJobUpdate, ScheduledJobResponse
from services.scheduler_service import scheduler_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ScheduledJobResponse)
async def create_scheduled_job(
    job_data: ScheduledJobCreate,
    db: Session = Depends(get_db)
):
    """Cria um novo job agendado"""
    try:
        logger.info(f"Criando job: {job_data.name} - {job_data.dict()}")
        # Validação das unidades permitidas
        valid_units = ["minutes", "hours", "days", "weeks", "months"]
        if job_data.interval_unit not in valid_units:
            raise HTTPException(
                status_code=400,
                detail=f"Unidade inválida. Use uma das seguintes: {', '.join(valid_units)}"
            )

        # Validação do valor do intervalo
        if job_data.interval_value <= 0:
            raise HTTPException(
                status_code=400,
                detail="O valor do intervalo deve ser maior que zero"
            )

        # Cria o job através do scheduler service
        job = await scheduler_service.create_job(
            name=job_data.name,
            description=job_data.description,
            task_type=job_data.task_type,
            interval_value=job_data.interval_value,
            interval_unit=job_data.interval_unit,
            task_config=job_data.task_config.dict()
        )

        return job

    except Exception as e:
        logger.error(f"Erro ao criar job agendado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ScheduledJobResponse])
async def list_scheduled_jobs(
    db: Session = Depends(get_db),
    is_active: bool = None
):
    """Lista todos os jobs agendados"""
    try:
        query = db.query(ScheduledJob).order_by(ScheduledJob.created_at.desc())

        if is_active is not None:
            query = query.filter(ScheduledJob.is_active == is_active)

        jobs = query.all()
        return jobs

    except Exception as e:
        logger.error(f"Erro ao listar jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=ScheduledJobResponse)
async def get_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Busca um job específico"""
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job

@router.put("/{job_id}", response_model=ScheduledJobResponse)
async def update_scheduled_job(
    job_id: int,
    job_data: ScheduledJobUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza um job existente"""
    try:
        # Validação das unidades se fornecida
        if job_data.interval_unit:
            valid_units = ["minutes", "hours", "days", "weeks", "months"]
            if job_data.interval_unit not in valid_units:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unidade inválida. Use uma das seguintes: {', '.join(valid_units)}"
                )

        # Validação do valor do intervalo se fornecido
        if job_data.interval_value is not None and job_data.interval_value <= 0:
            raise HTTPException(
                status_code=400,
                detail="O valor do intervalo deve ser maior que zero"
            )

        # Atualiza o job através do scheduler service
        job = await scheduler_service.update_job(job_id, **job_data.dict(exclude_unset=True))
        return job

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao atualizar job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{job_id}")
async def delete_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Remove um job agendado"""
    try:
        await scheduler_service.delete_job(job_id)
        return {"message": "Job removido com sucesso"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao remover job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/toggle")
async def toggle_job_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Ativa/desativa um job"""
    try:
        job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")

        new_status = not job.is_active
        await scheduler_service.update_job(job_id, is_active=new_status)

        return {
            "message": f"Job {'ativado' if new_status else 'desativado'} com sucesso",
            "is_active": new_status
        }

    except Exception as e:
        logger.error(f"Erro ao alterar status do job: {e}")
        raise HTTPException(status_code=500, detail=str(e))