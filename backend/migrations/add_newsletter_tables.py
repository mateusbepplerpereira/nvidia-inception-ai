"""Add newsletter tables

This migration adds tables for newsletter functionality:
- newsletter_emails: stores subscriber emails
- newsletter_sent: tracks sent newsletters
"""

import sys
import os

# Add the parent directory to sys.path so we can import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import engine

def upgrade():
    """Add newsletter tables"""

    # Create newsletter_emails table
    newsletter_emails_sql = """
    CREATE TABLE IF NOT EXISTS newsletter_emails (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        name VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    """

    # Create newsletter_sent table
    newsletter_sent_sql = """
    CREATE TABLE IF NOT EXISTS newsletter_sent (
        id SERIAL PRIMARY KEY,
        job_id INTEGER REFERENCES scheduled_jobs(id),
        email VARCHAR(255) NOT NULL,
        report_data JSONB,
        sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """

    # Create indexes for better performance
    newsletter_indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_newsletter_emails_email ON newsletter_emails(email);
    CREATE INDEX IF NOT EXISTS idx_newsletter_emails_is_active ON newsletter_emails(is_active);
    CREATE INDEX IF NOT EXISTS idx_newsletter_sent_job_id ON newsletter_sent(job_id);
    CREATE INDEX IF NOT EXISTS idx_newsletter_sent_email ON newsletter_sent(email);
    CREATE INDEX IF NOT EXISTS idx_newsletter_sent_sent_at ON newsletter_sent(sent_at);
    """

    with engine.connect() as conn:
        # Execute table creation
        conn.execute(text(newsletter_emails_sql))
        conn.execute(text(newsletter_sent_sql))
        conn.execute(text(newsletter_indexes_sql))
        conn.commit()

    print("✅ Newsletter tables created successfully")

def downgrade():
    """Remove newsletter tables"""

    # Drop tables (in reverse order due to foreign keys)
    drop_sql = """
    DROP TABLE IF EXISTS newsletter_sent;
    DROP TABLE IF EXISTS newsletter_emails;
    """

    with engine.connect() as conn:
        conn.execute(text(drop_sql))
        conn.commit()

    print("✅ Newsletter tables dropped successfully")

if __name__ == "__main__":
    print("Running newsletter tables migration...")
    upgrade()
    print("Migration completed!")