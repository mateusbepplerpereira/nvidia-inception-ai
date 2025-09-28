#!/usr/bin/env python3
"""
Migration script to add scheduler, notifications and logs tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings

def add_scheduler_tables():
    """Add scheduled_jobs, notifications and task_logs tables"""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Check if tables already exist
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('scheduled_jobs', 'notifications', 'task_logs')
        """))

        existing_tables = [row[0] for row in result.fetchall()]

        if 'scheduled_jobs' not in existing_tables:
            # Create scheduled_jobs table
            conn.execute(text("""
                CREATE TABLE scheduled_jobs (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    task_type VARCHAR(100) NOT NULL,
                    interval_value INTEGER NOT NULL,
                    interval_unit VARCHAR(20) NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    last_run TIMESTAMP WITH TIME ZONE,
                    next_run TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE
                )
            """))
            print("✅ Tabela 'scheduled_jobs' criada")
        else:
            print("✅ Tabela 'scheduled_jobs' já existe")

        if 'notifications' not in existing_tables:
            # Create notifications table
            conn.execute(text("""
                CREATE TABLE notifications (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50) DEFAULT 'info',
                    is_read BOOLEAN DEFAULT false,
                    task_id INTEGER REFERENCES agent_tasks(id),
                    job_id INTEGER REFERENCES scheduled_jobs(id),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            print("✅ Tabela 'notifications' criada")
        else:
            print("✅ Tabela 'notifications' já existe")

        if 'task_logs' not in existing_tables:
            # Create task_logs table
            conn.execute(text("""
                CREATE TABLE task_logs (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR(255) NOT NULL,
                    task_type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    message TEXT,
                    execution_time FLOAT,
                    scheduled_job_id INTEGER REFERENCES scheduled_jobs(id),
                    agent_task_id INTEGER REFERENCES agent_tasks(id),
                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            print("✅ Tabela 'task_logs' criada")
        else:
            print("✅ Tabela 'task_logs' já existe")

        # Create indexes for better performance
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_active ON scheduled_jobs(is_active)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_next_run ON scheduled_jobs(next_run)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_logs_created_at ON task_logs(created_at DESC)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_task_logs_task_type ON task_logs(task_type)"))
            print("✅ Índices criados")
        except Exception as e:
            print(f"⚠️  Aviso ao criar índices: {e}")

        conn.commit()
        print("✅ Transação commitada")

def add_trigger_for_updated_at():
    """Add trigger to update 'updated_at' field on scheduled_jobs"""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Create function to update updated_at
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """))

        # Create trigger
        conn.execute(text("""
            DROP TRIGGER IF EXISTS update_scheduled_jobs_updated_at ON scheduled_jobs;
            CREATE TRIGGER update_scheduled_jobs_updated_at
                BEFORE UPDATE ON scheduled_jobs
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """))

        conn.commit()
        print("✅ Trigger para updated_at criado")

if __name__ == "__main__":
    try:
        add_scheduler_tables()
        add_trigger_for_updated_at()
        print("🎉 Migração concluída com sucesso!")
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)