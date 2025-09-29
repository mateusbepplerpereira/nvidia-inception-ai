from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.connection import get_db
from database.models import ScheduledJob, TaskLog, Notification, Startup
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
            elif job.task_type == "newsletter":
                result = await self._execute_newsletter_task(job_id)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Atualiza job
            job.last_run = end_time
            job.next_run = end_time + timedelta(seconds=self._get_interval_seconds(job))

            db.commit()

            logger.info(f"Job '{job.name}' executado com sucesso em {execution_time:.2f}s")

            # Envia notificação via WebSocket após job completar
            await self._send_job_completion_notification(job_id, "success", execution_time)

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            db.commit()

            logger.error(f"Erro na execução do job '{job.name}': {e}")

            # Envia notificação de erro via WebSocket
            await self._send_job_completion_notification(job_id, "error", execution_time, str(e))

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

    async def _execute_newsletter_task(self, job_id: int):
        """Executa tarefa de newsletter - chama descoberta E DEPOIS envia email com resultados"""
        try:
            # Busca configuração do job
            db = next(get_db())
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
            if not job:
                raise ValueError("Job não encontrado")

            config = job.task_config or {}

            # 1. Executa descoberta ASSÍNCRONA e aguarda resultado REAL
            logger.info("Executando descoberta de startups para newsletter...")

            # Primeiro enfileira a descoberta (mantém assíncrono)
            discovery_result = await self._execute_startup_discovery_task(job_id)
            logger.info(f"Discovery task enfileirada: {discovery_result}")

            # 2. Aguarda REALMENTE a tarefa completar checando o banco
            import asyncio
            logger.info("Aguardando descoberta completar...")

            max_wait = 120  # 2 minutos máximo
            check_interval = 5  # verifica a cada 5 segundos
            elapsed = 0

            while elapsed < max_wait:
                await asyncio.sleep(check_interval)
                elapsed += check_interval

                # Verifica se há startups processadas recentemente (última 1 minuto)
                recent_time = datetime.now() - timedelta(minutes=1)
                recent_count = db.query(Startup).filter(
                    or_(
                        Startup.created_at >= recent_time,
                        Startup.updated_at >= recent_time
                    )
                ).count()

                logger.info(f"Aguardando descoberta... {elapsed}s - Startups recentes: {recent_count}")

                if recent_count > 0:
                    logger.info("Startups detectadas! Prosseguindo...")
                    break

            if elapsed >= max_wait:
                logger.warning("Timeout aguardando descoberta")

            logger.info("Descoberta aguardada, buscando resultados...")

            # 3. Agora busca as startups que foram processadas
            from database.models import StartupMetrics

            # Busca startups processadas nos últimos 3 minutos (janela maior para async)
            cutoff_recent = datetime.now() - timedelta(minutes=3)

            query = db.query(Startup).outerjoin(StartupMetrics)

            # Aplica filtros da configuração
            if config.get("country"):
                query = query.filter(Startup.country.ilike(f"%{config['country']}%"))
            if config.get("sector"):
                query = query.filter(Startup.sector.ilike(f"%{config['sector']}%"))

            # Busca startups descobertas AGORA
            recent_startups = query.filter(
                or_(
                    Startup.created_at >= cutoff_recent,
                    Startup.updated_at >= cutoff_recent
                )
            ).order_by(
                StartupMetrics.total_score.desc().nullslast(),
                Startup.created_at.desc()
            ).all()

            startup_count_real = len(recent_startups)
            logger.info(f"Encontradas {startup_count_real} startups para incluir no email")

            # 4. Prepara dados para email
            startup_data_for_email = []
            for startup in recent_startups:
                metrics = startup.metrics[0] if startup.metrics else None
                startup_data_for_email.append({
                    "name": startup.name or "N/A",
                    "sector": startup.sector or "N/A",
                    "country": startup.country or "N/A",
                    "city": startup.city or "N/A",
                    "founded_year": startup.founded_year or "N/A",
                    "website": startup.website or "N/A",
                    "description": startup.description[:150] + "..." if startup.description and len(startup.description) > 150 else (startup.description or "N/A"),
                    "ai_technologies": ", ".join(startup.ai_technologies) if startup.ai_technologies else "N/A",
                    "total_score": f"{metrics.total_score:.1f}" if metrics and metrics.total_score else "0.0"
                })

            # 5. Busca emails ativos e envia newsletter
            from database.models import NewsletterEmail, NewsletterSent
            emails = db.query(NewsletterEmail).filter(NewsletterEmail.is_active == True).all()

            if not emails:
                logger.warning("Nenhum email ativo encontrado na newsletter")
                return {"status": "warning", "message": "Nenhum email para enviar"}

            if startup_count_real == 0:
                logger.warning("Nenhuma startup encontrada para incluir no relatório")
                return {"status": "warning", "message": "Nenhuma startup encontrada"}

            # 6. Envia emails
            logger.info(f"Enviando newsletter para {len(emails)} destinatários...")
            from services.email_service import EmailService

            email_service = EmailService()
            email_addresses = [email.email for email in emails]

            success = email_service.send_newsletter_report(
                recipients=email_addresses,
                startup_data=startup_data_for_email,
                startup_count=startup_count_real
            )

            if success:
                # 7. Registra envios
                for email in emails:
                    newsletter_sent = NewsletterSent(
                        job_id=job_id,
                        email=email.email,
                        report_data={
                            "startup_count": startup_count_real,
                            "config": config,
                            "discovery_result": discovery_result,
                            "sent_at": datetime.now().isoformat()
                        }
                    )
                    db.add(newsletter_sent)

                db.commit()
                logger.info(f"Newsletter enviada com sucesso para {len(emails)} destinatários")
                return {"status": "success", "recipients": len(emails), "startups": startup_count_real}
            else:
                return {"status": "error", "message": "Falha no envio"}

        except Exception as e:
            logger.error(f"Erro na execução da newsletter: {e}")
            raise e
        finally:
            if 'db' in locals():
                db.close()

    async def _send_job_completion_notification(self, job_id: int, status: str, execution_time: float, error_msg: str = None):
        """Envia notificação via WebSocket quando job completa"""
        try:
            from services.notification_service import notification_service
            from database.models import ScheduledJob

            db = next(get_db())
            job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()

            if not job:
                return

            if status == "success":
                title = f"{job.name} - Concluída"
                message = f"Task executada com sucesso"
                notification_type = "success"
            else:
                title = f"{job.name} - Erro"
                message = f"Erro na execução: {error_msg}"
                notification_type = "error"

            # Enviar via WebSocket
            notification_data = {
                "id": None,  # Será definido depois se necessário
                "title": title,
                "message": message,
                "type": notification_type,
                "is_read": False,
                "created_at": datetime.now().isoformat()
            }

            await notification_service.send_notification_data(notification_data)
            logger.info(f"Notificação WebSocket enviada: {title}")

        except Exception as e:
            logger.error(f"Erro ao enviar notificação WebSocket: {e}")
        finally:
            if 'db' in locals():
                db.close()

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

            # Remover registros relacionados primeiro (para evitar foreign key constraint)
            from database.models import Notification, NewsletterSent

            # Remove newsletter records
            newsletter_records = db.query(NewsletterSent).filter(NewsletterSent.job_id == job_id).all()
            for record in newsletter_records:
                db.delete(record)

            if newsletter_records:
                logger.info(f"Removidos {len(newsletter_records)} registros de newsletter relacionados ao job {job_id}")

            # Remove notifications
            notifications = db.query(Notification).filter(Notification.job_id == job_id).all()
            for notification in notifications:
                db.delete(notification)

            if notifications:
                logger.info(f"Removidas {len(notifications)} notificações relacionadas ao job {job_id}")

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