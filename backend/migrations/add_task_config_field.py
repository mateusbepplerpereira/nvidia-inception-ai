#!/usr/bin/env python3
"""
Migration script to add task_config field to scheduled_jobs table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings

def add_task_config_field():
    """Add task_config field to scheduled_jobs table"""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Check if task_config column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'scheduled_jobs' AND column_name = 'task_config'
        """))

        if result.fetchone():
            print("✅ Campo 'task_config' já existe na tabela scheduled_jobs")
            return

        # Add task_config column
        conn.execute(text("""
            ALTER TABLE scheduled_jobs
            ADD COLUMN task_config JSON
        """))

        conn.commit()
        print("✅ Campo 'task_config' adicionado à tabela scheduled_jobs")

        # Update existing records with default config
        conn.execute(text("""
            UPDATE scheduled_jobs
            SET task_config = '{"country": "Brazil", "sector": null, "limit": 10, "search_strategy": "specific"}'::json
            WHERE task_config IS NULL
        """))

        conn.commit()
        print("✅ Registros existentes atualizados com configuração padrão")

if __name__ == "__main__":
    try:
        add_task_config_field()
        print("🎉 Migração concluída com sucesso!")
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)