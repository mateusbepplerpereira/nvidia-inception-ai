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

    # Se for do worker/scheduler, criar uma agent_task primeiro
    agent_task_id = None
    if from_worker:
        from database.models import AgentTask
        agent_task = AgentTask(
            task_type="startup_discovery",
            status="running",
            input_data={
                "country": country,
                "sector": sector,
                "limit": limit,
                "search_strategy": search_strategy,
                "from_scheduler": True,
                "job_id": job_id
            }
        )
        db.add(agent_task)
        db.commit()
        db.refresh(agent_task)
        agent_task_id = agent_task.id
        task_id = agent_task.id  # Usar o ID da agent_task
    else:
        agent_task_id = task_id

    # Criar log de início da tarefa
    from database.models import TaskLog
    from datetime import datetime
    start_time = datetime.now()

    # Verificar se job_id existe antes de referenciar
    valid_job_id = None
    job_name = None
    if from_worker and job_id:
        from database.models import ScheduledJob
        existing_job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if existing_job:
            valid_job_id = job_id
            job_name = existing_job.name
        else:
            print(f"WARNING: job_id {job_id} não existe na tabela scheduled_jobs. Usando None.")

    # Usar nome do job ou descrição genérica
    task_name = job_name if job_name else f"Descoberta Manual - {country}"
    task_type = f"scheduled_discovery_{sector.lower()}" if from_worker and sector else "manual_discovery"

    task_log = TaskLog(
        task_name=task_name,
        task_type=task_type,
        status="started",
        message=f"Iniciando descoberta de startups para {country}" + (f" - Setor: {sector}" if sector else ""),
        scheduled_job_id=valid_job_id,
        agent_task_id=agent_task_id,
        started_at=start_time
    )
    db.add(task_log)
    db.commit()
    db.refresh(task_log)

    # Atualizar mensagem com ID da task agent
    task_log.message = f"Task #{agent_task_id}: {task_log.message}"
    db.commit()

    try:
        # Update task to running
        service.update_task(task_id, "running")
        print(f"Iniciando orquestração para {country} - {sector or 'todos setores'} - Limit: {limit}")

        # Buscar startups existentes APENAS para exclusão (evitar redescobrir as mesmas)
        existing_valid = service.get_valid_startups_for_context(country, sector)
        existing_invalid = service.get_invalid_startups_for_context(country, sector)
        print(f"Exclusão: {len(existing_valid)} startups válidas já existem no setor {sector}")

        # Create orchestrator and run full pipeline
        # Nota: Sempre criar nova instância para evitar problemas de estado compartilhado
        try:
            orchestrator = StartupOrchestrator()
            print(f"Orchestrator criado com sucesso para task {agent_task_id}")
        except Exception as e:
            print(f"ERRO ao criar orchestrator: {e}")
            raise e
        result = orchestrator.run_orchestration(
            country=country,
            sector=sector,
            limit=limit,
            existing_valid=existing_valid,
            existing_invalid=existing_invalid,
            search_strategy=search_strategy
        )

        # Save results (apenas para tasks manuais, não do scheduler)
        if not from_worker:
            service.update_task(task_id, "completed", result)
        print(f"Orquestração concluída: {result.get('status')}")
        print(f"DEBUG - Result status type: {type(result.get('status'))}, value: '{result.get('status')}'")

        if result.get("status") == "success":
            # Salvar startups válidas
            valid_count = 0
            invalid_count = 0
            metrics_count = 0

            print(f"=== PROCESSANDO {len(result.get('results', {}).get('startup_metrics', []))} STARTUPS VALIDADAS ===")
            for i, startup_metrics in enumerate(result.get("results", {}).get("startup_metrics", []), 1):
                startup_data = startup_metrics["startup"]
                metrics_data = startup_metrics["metrics"]
                startup_name = startup_data.get('name', 'N/A')

                print(f"Processando startup {i}: {startup_name}")

                try:
                    # Salvar startup
                    saved_startup = service.save_startup_from_discovery(startup_data)
                    valid_count += 1
                    print(f"Startup {startup_name} salva com sucesso (valid_count: {valid_count})")

                    # Salvar métricas
                    service.save_startup_metrics(saved_startup.id, metrics_data)
                    metrics_count += 1
                    print(f"Métricas salvas para {startup_name} (metrics_count: {metrics_count})")

                except Exception as e:
                    print(f"ERRO ao salvar startup {startup_name}: {e}")
                    import traceback
                    print(f"Traceback: {traceback.format_exc()}")

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
            task_log.message = f"Task #{agent_task_id}: Orquestração concluída com sucesso: {valid_count} startups válidas, {invalid_count} inválidas"
            task_log.completed_at = end_time
            task_log.execution_time = execution_time

            # Atualizar agent_task status para completed se existir
            if from_worker and agent_task_id:
                from database.models import AgentTask
                agent_task = db.query(AgentTask).filter(AgentTask.id == agent_task_id).first()
                if agent_task:
                    agent_task.status = "completed"
                    agent_task.output_data = {
                        "valid_startups": valid_count,
                        "invalid_startups": invalid_count,
                        "execution_time": execution_time
                    }
                    agent_task.completed_at = end_time

            # Commit das alterações
            db.commit()

            # Criar notificação de sucesso (será enviada no finally)
            from database.models import Notification
            notification_title = f"{task_name} - Concluída" if job_name else "Descoberta de Startups Concluída"
            notification = Notification(
                title=notification_title,
                message=f"Encontradas {valid_count} startups válidas para {country}" + (f" no setor {sector}" if sector else "") + f" ({invalid_count} inválidas)",
                type="success",
                task_id=agent_task_id,
                job_id=valid_job_id
            )
            db.add(notification)
            db.commit()

            print(f"=== RESULTADO FINAL ===")
            print(f"{valid_count} startups válidas salvas")
            print(f"{metrics_count} métricas calculadas")
            print(f"{invalid_count} startups inválidas")
            print(f"=== FIM DO PROCESSAMENTO ===")

        else:
            # Atualizar log de erro
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            task_log.status = "failed"
            task_log.message = f"Task #{agent_task_id}: Orquestração falhou: {result.get('error', 'Erro desconhecido')}"
            task_log.completed_at = end_time
            task_log.execution_time = execution_time

            # Atualizar agent_task status para failed se existir
            if from_worker and agent_task_id:
                from database.models import AgentTask
                agent_task = db.query(AgentTask).filter(AgentTask.id == agent_task_id).first()
                if agent_task:
                    agent_task.status = "failed"
                    agent_task.error_message = result.get('error', 'Erro desconhecido')
                    agent_task.completed_at = end_time

            # Commit das alterações
            db.commit()

            # Criar notificação de erro (será enviada no finally)
            from database.models import Notification
            notification_title = f"{task_name} - Erro" if job_name else "Erro na Descoberta de Startups"
            notification = Notification(
                title=notification_title,
                message=f"Falha na descoberta para {country}: {result.get('error', 'Erro desconhecido')}",
                type="error",
                task_id=agent_task_id,
                job_id=valid_job_id
            )
            db.add(notification)
            db.commit()

    except Exception as e:
        error_msg = f"Erro na orquestração: {str(e)}"
        print(f"Erro na task {agent_task_id}: {error_msg}")

        # Atualizar logs
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        task_log.status = "failed"
        task_log.message = f"Task #{agent_task_id}: Erro na orquestração: {str(e)}"
        task_log.completed_at = end_time
        task_log.execution_time = execution_time

        # Atualizar agent_task se existir
        if from_worker and agent_task_id:
            from database.models import AgentTask
            agent_task = db.query(AgentTask).filter(AgentTask.id == agent_task_id).first()
            if agent_task:
                agent_task.status = "failed"
                agent_task.error_message = str(e)
                agent_task.completed_at = end_time

        db.commit()

        # Criar notificação de erro
        from database.models import Notification
        notification_title = f"{task_name} - Erro" if job_name else "Erro na Descoberta de Startups"
        notification = Notification(
            title=notification_title,
            message=f"Erro na orquestração: {str(e)}",
            type="error",
            task_id=agent_task_id,
            job_id=valid_job_id
        )
        db.add(notification)
        db.commit()

        # Envia notificação via WebSocket
        from services.notification_service import notification_service
        import asyncio
        try:
            asyncio.create_task(notification_service.send_notification(notification))
        except:
            pass  # Se WebSocket falhar, não quebrar a execução

        # Atualizar log de erro
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        task_log.status = "failed"
        task_log.message = error_msg
        task_log.completed_at = end_time
        task_log.execution_time = execution_time

        # Notificação já foi criada acima, não duplicar

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