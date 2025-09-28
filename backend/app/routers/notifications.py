from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from database.models import Notification
from schemas.agent import NotificationResponse
from services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint para notificações em tempo real"""
    await websocket.accept()
    notification_service.add_websocket_connection(websocket)

    try:
        while True:
            # Mantém a conexão ativa
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_service.remove_websocket_connection(websocket)
        logger.info("Cliente WebSocket desconectado")

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Lista notificações com paginação"""
    try:
        notifications = notification_service.get_notifications(limit=limit, offset=offset)
        return notifications
    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
async def get_unread_count():
    """Retorna o número de notificações não lidas"""
    try:
        count = notification_service.get_unread_count()
        return {"unread_count": count}
    except Exception as e:
        logger.error(f"Erro ao buscar contagem de não lidas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Marca uma notificação como lida"""
    try:
        notification_service.mark_as_read(notification_id)
        return {"message": "Notificação marcada como lida"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao marcar notificação como lida: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mark-all-read")
async def mark_all_notifications_as_read():
    """Marca todas as notificações como lidas"""
    try:
        notification_service.mark_all_as_read()
        return {"message": "Todas as notificações marcadas como lidas"}
    except Exception as e:
        logger.error(f"Erro ao marcar todas como lidas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Remove uma notificação"""
    try:
        notification_service.delete_notification(notification_id)
        return {"message": "Notificação removida com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao remover notificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))