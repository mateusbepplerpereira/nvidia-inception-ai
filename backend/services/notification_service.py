from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Notification
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.websocket_connections: List[Any] = []

    def add_websocket_connection(self, websocket):
        """Adiciona uma conexão WebSocket"""
        self.websocket_connections.append(websocket)
        logger.info(f"Nova conexão WebSocket adicionada. Total: {len(self.websocket_connections)}")

    def remove_websocket_connection(self, websocket):
        """Remove uma conexão WebSocket"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
            logger.info(f"Conexão WebSocket removida. Total: {len(self.websocket_connections)}")

    async def send_notification(self, notification: Notification):
        """Envia notificação via WebSocket para todos os clientes conectados"""
        if not self.websocket_connections:
            return

        notification_data = {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat() if notification.created_at else None
        }

        await self.send_notification_data(notification_data)

    async def send_notification_data(self, notification_data: dict):
        """Envia dados de notificação via WebSocket para todos os clientes conectados"""
        if not self.websocket_connections:
            return

        message = json.dumps({
            "type": "notification",
            "data": notification_data
        })

        # Remove conexões fechadas
        active_connections = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
                active_connections.append(websocket)
            except Exception as e:
                logger.warning(f"Erro ao enviar notificação via WebSocket: {e}")

        self.websocket_connections = active_connections
        logger.info(f"Notificação enviada para {len(active_connections)} clientes")

    def create_notification(self, title: str, message: str, type: str = "info",
                          task_id: int = None, job_id: int = None) -> Notification:
        """Cria uma nova notificação no banco de dados"""
        db = next(get_db())
        try:
            notification = Notification(
                title=title,
                message=message,
                type=type,
                task_id=task_id,
                job_id=job_id,
                is_read=False
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(f"Notificação criada: {title}")
            return notification

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao criar notificação: {e}")
            raise e
        finally:
            db.close()

    def get_notifications(self, limit: int = 50, offset: int = 0) -> List[Notification]:
        """Busca notificações com paginação"""
        db = next(get_db())
        try:
            notifications = db.query(Notification)\
                .order_by(Notification.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            return notifications
        finally:
            db.close()

    def get_unread_count(self) -> int:
        """Retorna o número de notificações não lidas"""
        db = next(get_db())
        try:
            count = db.query(Notification)\
                .filter(Notification.is_read == False)\
                .count()
            return count
        finally:
            db.close()

    def mark_as_read(self, notification_id: int):
        """Marca uma notificação como lida"""
        db = next(get_db())
        try:
            notification = db.query(Notification)\
                .filter(Notification.id == notification_id)\
                .first()

            if notification:
                notification.is_read = True
                db.commit()
                logger.info(f"Notificação {notification_id} marcada como lida")
            else:
                raise ValueError("Notificação não encontrada")

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao marcar notificação como lida: {e}")
            raise e
        finally:
            db.close()

    def mark_all_as_read(self):
        """Marca todas as notificações como lidas"""
        db = next(get_db())
        try:
            db.query(Notification)\
                .filter(Notification.is_read == False)\
                .update({"is_read": True})
            db.commit()
            logger.info("Todas as notificações marcadas como lidas")

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao marcar todas as notificações como lidas: {e}")
            raise e
        finally:
            db.close()

    def delete_notification(self, notification_id: int):
        """Remove uma notificação"""
        db = next(get_db())
        try:
            notification = db.query(Notification)\
                .filter(Notification.id == notification_id)\
                .first()

            if notification:
                db.delete(notification)
                db.commit()
                logger.info(f"Notificação {notification_id} removida")
            else:
                raise ValueError("Notificação não encontrada")

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao remover notificação: {e}")
            raise e
        finally:
            db.close()

# Instância global do serviço de notificações
notification_service = NotificationService()