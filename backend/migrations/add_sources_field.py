#!/usr/bin/env python3
"""
Migration script to add sources field to startups table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import settings

def add_sources_field():
    """Add sources field to startups table"""
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Check if sources column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'startups' AND column_name = 'sources'
        """))

        if result.fetchone():
            print("✅ Campo 'sources' já existe na tabela startups")
            return

        # Add sources column
        conn.execute(text("""
            ALTER TABLE startups
            ADD COLUMN sources JSON
        """))

        conn.commit()
        print("✅ Campo 'sources' adicionado à tabela startups")

        # Update existing records with default empty sources
        conn.execute(text("""
            UPDATE startups
            SET sources = '{}'::json
            WHERE sources IS NULL
        """))

        conn.commit()
        print("✅ Registros existentes atualizados com sources vazios")

if __name__ == "__main__":
    try:
        add_sources_field()
        print("🎉 Migração concluída com sucesso!")
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        sys.exit(1)