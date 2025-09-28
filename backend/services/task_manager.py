import asyncio
import threading
from typing import Dict, Callable, Any
from queue import Queue
import time
from datetime import datetime
from sqlalchemy.orm import Session
from database.connection import get_db
from services.agent_service import AgentService
from agents.orchestrator import StartupOrchestrator

class TaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.task_queue = Queue()
            self.worker_running = False
            self.worker_thread = None
            self.initialized = True

    def start_worker(self):
        """Inicia o worker para processamento de tasks"""
        if not self.worker_running:
            self.worker_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("Task worker iniciado")

    def stop_worker(self):
        """Para o worker"""
        self.worker_running = False
        if self.worker_thread:
            self.worker_thread.join()
            print("Task worker parado")

    def enqueue_task(self, task_id: int, task_func: Callable, *args, **kwargs):
        """Adiciona uma task na fila"""
        self.task_queue.put({
            'task_id': task_id,
            'function': task_func,
            'args': args,
            'kwargs': kwargs,
            'created_at': datetime.now()
        })
        print(f"Task {task_id} adicionada à fila (tamanho: {self.task_queue.qsize()})")

    def _worker_loop(self):
        """Loop principal do worker"""
        print("Worker loop iniciado")

        while self.worker_running:
            try:
                # Pega task da fila (bloqueia por 1 segundo)
                task = self.task_queue.get(timeout=1.0)

                print(f"Processando task {task['task_id']}")

                # Executa a task
                try:
                    task['function'](*task['args'], **task['kwargs'])
                    print(f"Task {task['task_id']} concluída")
                except Exception as e:
                    print(f"Erro na task {task['task_id']}: {e}")
                finally:
                    self.task_queue.task_done()

            except:
                # Timeout - continua o loop
                continue

        print("Worker loop finalizado")

    def get_queue_size(self) -> int:
        """Retorna o tamanho atual da fila"""
        return self.task_queue.qsize()

    def is_worker_running(self) -> bool:
        """Verifica se o worker está rodando"""
        return self.worker_running

# Singleton instance
task_manager = TaskManager()

# Função para executar orquestração completa
def process_orchestration_task(task_id: int, country: str, sector: str, limit: int = 5, from_worker: bool = False, job_id: int = None, search_strategy: str = "specific"):
    """Processa uma task de orquestração completa (Discovery → Validation → Metrics)"""

    # Get database session
    db = next(get_db())
    service = AgentService(db)

    # Criar log de início da tarefa
    from database.models import TaskLog
    from datetime import datetime
    start_time = datetime.now()

    task_log = TaskLog(
        task_name=f"Orquestração de Startups - {country}",
        task_type="startup_discovery",
        status="started",
        message=f"Iniciando descoberta de startups para {country}" + (f" - Setor: {sector}" if sector else ""),
        scheduled_job_id=job_id if from_worker else None,
        agent_task_id=task_id if not from_worker and task_id > 0 else None,
        started_at=start_time
    )
    db.add(task_log)
    db.commit()
    db.refresh(task_log)

    # Atualizar mensagem com ID da task
    task_log.message = f"Task {task_log.id}: {task_log.message}"
    db.commit()

    try:
        # Update task to running
        service.update_task(task_id, "running")
        print(f"Iniciando orquestração para {country} - {sector or 'todos setores'} - Limit: {limit}")

        # Buscar startups já processadas para contexto
        existing_valid = service.get_valid_startups_for_context(country, sector)
        existing_invalid = service.get_invalid_startups_for_context(country, sector)

        # Create orchestrator and run full pipeline
        orchestrator = StartupOrchestrator()
        result = orchestrator.run_orchestration(
            country=country,
            sector=sector,
            limit=limit,
            existing_valid=existing_valid,
            existing_invalid=existing_invalid,
            search_strategy=search_strategy
        )

        # Save results
        service.update_task(task_id, "completed", result)
        print(f"Orquestração concluída: {result.get('status')}")

        if result.get("status") == "success":
            # Salvar startups válidas
            valid_count = 0
            invalid_count = 0
            metrics_count = 0

            for startup_metrics in result.get("results", {}).get("startup_metrics", []):
                startup_data = startup_metrics["startup"]
                metrics_data = startup_metrics["metrics"]

                try:
                    # Salvar startup
                    saved_startup = service.save_startup_from_discovery(startup_data)
                    valid_count += 1

                    # Salvar métricas
                    service.save_startup_metrics(saved_startup.id, metrics_data)
                    metrics_count += 1

                except Exception as e:
                    print(f"Erro ao salvar startup {startup_data.get('name')}: {e}")

            # Salvar startups inválidas com insights detalhados
            for invalid_startup in result.get("results", {}).get("invalid_startups", []):
                try:
                    service.save_invalid_startup(invalid_startup)
                    invalid_count += 1
                except Exception as e:
                    print(f"Erro ao salvar startup inválida {invalid_startup.get('name')}: {e}")

            # Atualizar log de sucesso
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            task_log.status = "completed"
            task_log.message = f"Task {task_log.id}: Orquestração concluída com sucesso: {valid_count} startups válidas, {invalid_count} inválidas"
            task_log.completed_at = end_time
            task_log.execution_time = execution_time

            # Criar notificação de sucesso
            from database.models import Notification
            notification = Notification(
                title="Descoberta de Startups Concluída",
                message=f"Task {task_log.id}: Encontradas {valid_count} startups válidas para {country}" + (f" no setor {sector}" if sector else ""),
                type="success",
                task_id=task_id if not from_worker and task_id > 0 else None,
                job_id=job_id if from_worker else None
            )
            db.add(notification)

            print(f"{valid_count} startups válidas salvas")
            print(f"{metrics_count} métricas calculadas")
            print(f"{invalid_count} startups inválidas")

        else:
            # Atualizar log de erro
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            task_log.status = "failed"
            task_log.message = f"Task {task_log.id}: Orquestração falhou: {result.get('error', 'Erro desconhecido')}"
            task_log.completed_at = end_time
            task_log.execution_time = execution_time

            # Criar notificação de erro
            from database.models import Notification
            notification = Notification(
                title="Erro na Descoberta de Startups",
                message=f"Task {task_log.id}: Falha na descoberta para {country}: {result.get('error', 'Erro desconhecido')}",
                type="error",
                task_id=task_id if not from_worker and task_id > 0 else None,
                job_id=job_id if from_worker else None
            )
            db.add(notification)

    except Exception as e:
        error_msg = f"Erro na orquestração: {str(e)}"
        print(f"{error_msg}")
        service.update_task(task_id, "failed", error_message=error_msg)

        # Atualizar log de erro
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        task_log.status = "failed"
        task_log.message = error_msg
        task_log.completed_at = end_time
        task_log.execution_time = execution_time

        # Criar notificação de erro
        from database.models import Notification
        notification = Notification(
            title="Erro na Descoberta de Startups",
            message=f"Falha na descoberta para {country}: {str(e)}",
            type="error",
            task_id=task_id,
            job_id=job_id if from_worker else None
        )
        db.add(notification)

    finally:
        # Salvar todas as alterações e enviar notificação via WebSocket
        try:
            db.commit()

            # Enviar notificação via WebSocket se houver uma
            if 'notification' in locals():
                try:
                    from services.notification_service import notification_service
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(notification_service.send_notification(notification))
                    loop.close()
                except Exception as ws_error:
                    print(f"Erro ao enviar notificação via WebSocket: {ws_error}")

        except Exception as e:
            print(f"Erro ao salvar logs/notificações: {e}")
        finally:
            db.close()

# Auto-start worker when module is imported
if not task_manager.is_worker_running():
    task_manager.start_worker()