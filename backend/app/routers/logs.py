from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models import TaskLog
from schemas.agent import TaskLogResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[TaskLogResponse])
async def get_task_logs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista logs de tarefas com paginação e filtros"""
    try:
        query = db.query(TaskLog).order_by(TaskLog.created_at.desc())

        # Aplicar filtros se fornecidos
        if status:
            query = query.filter(TaskLog.status == status)

        if task_type:
            query = query.filter(TaskLog.task_type == task_type)

        # Aplicar paginação
        logs = query.offset(offset).limit(limit).all()

        return logs

    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_logs_stats(
    db: Session = Depends(get_db)
):
    """Retorna estatísticas dos logs"""
    try:
        from sqlalchemy import func

        # Total de logs
        total_logs = db.query(TaskLog).count()

        # Logs por status
        logs_by_status = db.query(
            TaskLog.status,
            func.count(TaskLog.id)
        ).group_by(TaskLog.status).all()

        # Logs por tipo de tarefa
        logs_by_type = db.query(
            TaskLog.task_type,
            func.count(TaskLog.id)
        ).group_by(TaskLog.task_type).all()

        # Tempo médio de execução
        avg_execution_time = db.query(
            func.avg(TaskLog.execution_time)
        ).filter(TaskLog.execution_time.isnot(None)).scalar()

        # Logs das últimas 24h
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_logs = db.query(TaskLog).filter(
            TaskLog.created_at >= yesterday
        ).count()

        return {
            "total_logs": total_logs,
            "recent_logs_24h": recent_logs,
            "avg_execution_time": float(avg_execution_time) if avg_execution_time else 0,
            "by_status": dict(logs_by_status),
            "by_type": dict(logs_by_type)
        }

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas dos logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{log_id}", response_model=TaskLogResponse)
async def get_task_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """Busca um log específico"""
    log = db.query(TaskLog).filter(TaskLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado")
    return log

@router.delete("/{log_id}")
async def delete_task_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """Remove um log específico"""
    try:
        log = db.query(TaskLog).filter(TaskLog.id == log_id).first()
        if not log:
            raise HTTPException(status_code=404, detail="Log não encontrado")

        db.delete(log)
        db.commit()

        return {"message": "Log removido com sucesso"}

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao remover log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/")
async def clear_logs(
    status: Optional[str] = None,
    older_than_days: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Remove logs com base em critérios"""
    try:
        query = db.query(TaskLog)

        # Filtro por status
        if status:
            query = query.filter(TaskLog.status == status)

        # Filtro por data
        if older_than_days:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            query = query.filter(TaskLog.created_at < cutoff_date)

        # Conta quantos logs serão removidos
        count = query.count()

        # Remove os logs
        query.delete()
        db.commit()

        return {
            "message": f"{count} logs removidos com sucesso",
            "removed_count": count
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao limpar logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))