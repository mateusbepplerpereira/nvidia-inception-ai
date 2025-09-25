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
def process_orchestration_task(task_id: int, country: str, sector: str, limit: int = 5):
    """Processa uma task de orquestração completa (Discovery → Validation → Metrics)"""

    # Get database session
    db = next(get_db())
    service = AgentService(db)

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
            existing_invalid=existing_invalid
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
                except Exception as e:
                    print(f"Erro ao salvar startup inválida {invalid_startup.get('name')}: {e}")

            print(f"{valid_count} startups válidas salvas")
            print(f"{metrics_count} métricas calculadas")
            print(f"{result.get('results', {}).get('invalid_count', 0)} startups inválidas")

    except Exception as e:
        error_msg = f"Erro na orquestração: {str(e)}"
        print(f"{error_msg}")
        service.update_task(task_id, "failed", error_message=error_msg)
    finally:
        db.close()

# Auto-start worker when module is imported
if not task_manager.is_worker_running():
    task_manager.start_worker()