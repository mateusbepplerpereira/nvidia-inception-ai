import asyncio
import threading
from typing import Dict, Callable, Any
from queue import Queue
import time
from datetime import datetime
from sqlalchemy.orm import Session
from database.connection import get_db
from services.agent_service import AgentService
from agents.direct_openai import DirectOpenAIAgent

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
            print("📋 Task worker iniciado")

    def stop_worker(self):
        """Para o worker"""
        self.worker_running = False
        if self.worker_thread:
            self.worker_thread.join()
            print("📋 Task worker parado")

    def enqueue_task(self, task_id: int, task_func: Callable, *args, **kwargs):
        """Adiciona uma task na fila"""
        self.task_queue.put({
            'task_id': task_id,
            'function': task_func,
            'args': args,
            'kwargs': kwargs,
            'created_at': datetime.now()
        })
        print(f"📋 Task {task_id} adicionada à fila (tamanho: {self.task_queue.qsize()})")

    def _worker_loop(self):
        """Loop principal do worker"""
        print("🔄 Worker loop iniciado")

        while self.worker_running:
            try:
                # Pega task da fila (bloqueia por 1 segundo)
                task = self.task_queue.get(timeout=1.0)

                print(f"⚙️  Processando task {task['task_id']}")

                # Executa a task
                try:
                    task['function'](*task['args'], **task['kwargs'])
                    print(f"✅ Task {task['task_id']} concluída")
                except Exception as e:
                    print(f"❌ Erro na task {task['task_id']}: {e}")
                finally:
                    self.task_queue.task_done()

            except:
                # Timeout - continua o loop
                continue

        print("🔄 Worker loop finalizado")

    def get_queue_size(self) -> int:
        """Retorna o tamanho atual da fila"""
        return self.task_queue.qsize()

    def is_worker_running(self) -> bool:
        """Verifica se o worker está rodando"""
        return self.worker_running

# Singleton instance
task_manager = TaskManager()

# Função para executar discovery de forma assíncrona
def process_discovery_task(task_id: int, country: str, sector: str):
    """Processa uma task de discovery"""

    # Get database session
    db = next(get_db())
    service = AgentService(db)

    try:
        # Update task to running
        service.update_task(task_id, "running")
        print(f"🚀 Iniciando discovery para {country} - {sector or 'todos setores'}")

        # Create agent and run discovery
        agent = DirectOpenAIAgent()
        result = agent.discover_startups(country, sector)

        # Save results
        service.update_task(task_id, "completed", result)
        print(f"📊 Discovery concluída: {result.get('count', 0)} startups")

        # Process and save startups
        if result.get("status") == "success" and "startups" in result:
            saved_count = 0
            for startup_data in result["startups"]:
                try:
                    service.save_startup_from_discovery(startup_data)
                    saved_count += 1
                except Exception as e:
                    print(f"⚠️  Erro ao salvar startup {startup_data.get('name')}: {e}")

            print(f"💾 {saved_count} startups salvas no banco")

    except Exception as e:
        error_msg = f"Erro na discovery: {str(e)}"
        print(f"❌ {error_msg}")
        service.update_task(task_id, "failed", error_message=error_msg)
    finally:
        db.close()

# Auto-start worker when module is imported
if not task_manager.is_worker_running():
    task_manager.start_worker()