#!/usr/bin/env python3
"""
Migration: Add CEO and CTO fields to startups table
"""

import os
import sys
sys.path.append('/app')

import psycopg2
from database.connection import DATABASE_URL

def run_migration():
    """Adiciona campos CEO e CTO na tabela startups"""

    # Parse DATABASE_URL
    db_url = DATABASE_URL.replace("postgresql://", "")
    user_pass, host_db = db_url.split("@")
    user, password = user_pass.split(":")
    host_port, database = host_db.split("/")
    host, port = host_port.split(":")

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

        cursor = conn.cursor()

        print("🔄 Executando migração...")

        # Add CEO fields
        try:
            cursor.execute("ALTER TABLE startups ADD COLUMN ceo_name VARCHAR(255);")
            print("✅ Coluna ceo_name adicionada")
        except psycopg2.errors.DuplicateColumn:
            print("⚠️  Coluna ceo_name já existe")

        try:
            cursor.execute("ALTER TABLE startups ADD COLUMN ceo_linkedin VARCHAR(500);")
            print("✅ Coluna ceo_linkedin adicionada")
        except psycopg2.errors.DuplicateColumn:
            print("⚠️  Coluna ceo_linkedin já existe")

        # Add CTO fields
        try:
            cursor.execute("ALTER TABLE startups ADD COLUMN cto_name VARCHAR(255);")
            print("✅ Coluna cto_name adicionada")
        except psycopg2.errors.DuplicateColumn:
            print("⚠️  Coluna cto_name já existe")

        try:
            cursor.execute("ALTER TABLE startups ADD COLUMN cto_linkedin VARCHAR(500);")
            print("✅ Coluna cto_linkedin adicionada")
        except psycopg2.errors.DuplicateColumn:
            print("⚠️  Coluna cto_linkedin já existe")

        # Commit changes
        conn.commit()

        # Verify table structure
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'startups'
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()
        print("\n📋 Estrutura da tabela startups:")
        for col_name, col_type in columns:
            print(f"   • {col_name}: {col_type}")

        cursor.close()
        conn.close()

        print("\n✅ Migração concluída com sucesso!")

    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        return False

    return True

if __name__ == "__main__":
    run_migration()