from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import ScheduledJob, TaskLog, Notification
# Imports removidos para evitar dependências circulares - serão importados localmente quando necessário
import asyncio
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Inicia o scheduler e carrega os jobs existentes"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler iniciado")

        # Carrega jobs existentes do banco
        asyncio.create_task(self._load_existing_jobs())

    def stop(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler parado")

    async def _load_existing_jobs(self):
        """Carrega jobs ativos do banco de dados"""
        db = next(get_db())
        try:
            jobs = db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()
            for job in jobs:
                await self._schedule_job(job)
            logger.info(f"Carregados {len(jobs)} jobs ativos")
        except Exception as e:
            logger.error(f"Erro ao carregar jobs existentes: {e}")
        finally:
            db.close()

    async def _schedule_job(self, job: ScheduledJob):
        """Agenda um job específico"""
        try:
            # Converte unidade para segundos
            unit_to_seconds = {
                'minutes': 60,
                'hours': 3600,
                'days': 86400,
                'weeks': 604800,
                'months': 2628000  # aproximadamente 30.4 dias
            }

            interval_seconds = job.interval_value * unit_to_seconds.get(job.interval_unit, 3600)

            # Remove job existente se já estiver agendado
            if self.scheduler.get_job(str(job.id)):
                self.scheduler.remove_job(str(job.id))

            # Agenda o novo job
            self.scheduler.add_job(
                func=self._execute_job,
                args=[job.id],
                trigger=IntervalTrigger(seconds=interval_seconds),
                id=str(job.id),
                name=job.name,
                next_run_time=datetime.now() if job.next_run is None else job.next_run
            )

            logger.info(f"Job '{job.name}' agendado para executar a cada {job.interval_value} {job.interval_unit}")

        except Exception as e:
            logger.error(f"Erro ao agendar job {job.id}: {e}")

    async def _execute_job(self, job_id: int):
        """Executa um job agendado"""
        db = next(get_db())
        start_time = datetime.now()

        try:
            # Busca o job no banco
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job or not job.is_active:
                return

            logger.info(f"Iniciando execução do job: {job.name}")

            # Executa a tarefa baseada no tipo
            result = None
            if job.task_type == "startup_discovery":
                result = await self._execute_startup_discovery_task(job_id)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Atualiza job
            job.last_run = end_time
            job.next_run = end_time + timedelta(seconds=self._get_interval_seconds(job))

            db.commit()

            logger.info(f"Job '{job.name}' executado com sucesso em {execution_time:.2f}s")

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            db.commit()

            logger.error(f"Erro na execução do job '{job.name}': {e}")

        finally:
            db.close()

    async def _execute_startup_discovery_task(self, job_id: int):
        """Executa tarefa de descoberta de startups"""
        try:
            # Busca configuração do job
            db = next(get_db())
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job:
                raise ValueError("Job não encontrado")

            # Extrai parâmetros da configuração
            config = job.task_config or {}
            country = config.get("country", "")
            sector = config.get("sector", "")
            limit = config.get("limit", 10)

            # Determina strategy automaticamente baseado nos parâmetros
            if not country and not sector:
                search_strategy = "global_market_demand"  # Busca global por setores emergentes
            elif not sector:
                search_strategy = "market_demand"  # Busca setores emergentes no país especificado
            elif not country:
                search_strategy = "global"  # Busca global para o setor específico
            else:
                search_strategy = "specific"  # Busca específica por país e setor

            # Import local para evitar dependência circular
            from services.task_manager import task_manager, process_orchestration_task

            # Enfileira a tarefa no task manager com parâmetros configuráveis
            task_manager.enqueue_task(
                0,  # task_id temporário - será criado internamente
                process_orchestration_task,
                0,  # task_id temporário
                country,
                sector,
                limit,
                True,  # from_worker
                job_id,  # job_id
                search_strategy  # novo parâmetro
            )

            db.close()
            return {"status": "success", "message": "Task enqueued"}
        except Exception as e:
            raise e

    def _get_interval_seconds(self, job: ScheduledJob) -> int:
        """Converte intervalo do job para segundos"""
        unit_to_seconds = {
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800,
            'months': 2628000
        }
        return job.interval_value * unit_to_seconds.get(job.interval_unit, 3600)

    async def create_job(self, name: str, description: str, task_type: str,
                        interval_value: int, interval_unit: str, task_config: dict = None) -> ScheduledJob:
        """Cria um novo job agendado"""
        db = next(get_db())
        try:
            # Calcula próxima execução
            interval_seconds = self._get_interval_seconds_static(interval_value, interval_unit)
            next_run = datetime.now() + timedelta(seconds=interval_seconds)

            job = ScheduledJob(
                name=name,
                description=description,
                task_type=task_type,
                interval_value=interval_value,
                interval_unit=interval_unit,
                task_config=task_config,
                next_run=next_run,
                is_active=True
            )

            db.add(job)
            db.commit()
            db.refresh(job)

            # Agenda o job
            await self._schedule_job(job)

            logger.info(f"Job criado: {name}")
            return job

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao criar job: {e}")
            raise e
        finally:
            db.close()

    def _get_interval_seconds_static(self, interval_value: int, interval_unit: str) -> int:
        """Versão estática para calcular segundos"""
        unit_to_seconds = {
            'minutes': 60,
            'hours': 3600,
            'days': 86400,
            'weeks': 604800,
            'months': 2628000
        }
        return interval_value * unit_to_seconds.get(interval_unit, 3600)

    async def update_job(self, job_id: int, **kwargs) -> ScheduledJob:
        """Atualiza um job existente"""
        db = next(get_db())
        try:
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job:
                raise ValueError("Job não encontrado")

            # Atualiza campos
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            # Recalcula próxima execução se intervalo mudou
            if 'interval_value' in kwargs or 'interval_unit' in kwargs:
                interval_seconds = self._get_interval_seconds(job)
                job.next_run = datetime.now() + timedelta(seconds=interval_seconds)

            db.commit()
            db.refresh(job)

            # Re-agenda o job
            if job.is_active:
                await self._schedule_job(job)
            else:
                # Remove job se foi desativado
                if self.scheduler.get_job(str(job.id)):
                    self.scheduler.remove_job(str(job.id))

            logger.info(f"Job atualizado: {job.name}")
            return job

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao atualizar job: {e}")
            raise e
        finally:
            db.close()

    async def delete_job(self, job_id: int):
        """Remove um job"""
        db = next(get_db())
        try:
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job:
                raise ValueError("Job não encontrado")

            # Remove do scheduler
            if self.scheduler.get_job(str(job.id)):
                self.scheduler.remove_job(str(job.id))

            # Remove do banco
            db.delete(job)
            db.commit()

            logger.info(f"Job removido: {job.name}")

        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao remover job: {e}")
            raise e
        finally:
            db.close()

# Instância global do scheduler
scheduler_service = SchedulerService()