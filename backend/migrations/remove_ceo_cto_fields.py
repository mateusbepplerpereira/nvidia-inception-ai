"""
Remove CEO and CTO fields from database tables
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nvidia_user:nvidia_pass@localhost:5432/nvidia_inception_db"
)

def remove_ceo_cto_fields():
    """Remove CEO/CTO fields from startups and invalid_startups tables"""

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Remove from startups table
        try:
            conn.execute(text("ALTER TABLE startups DROP COLUMN IF EXISTS ceo_name CASCADE"))
            conn.execute(text("ALTER TABLE startups DROP COLUMN IF EXISTS ceo_linkedin CASCADE"))
            conn.execute(text("ALTER TABLE startups DROP COLUMN IF EXISTS cto_name CASCADE"))
            conn.execute(text("ALTER TABLE startups DROP COLUMN IF EXISTS cto_linkedin CASCADE"))
            conn.commit()
            print("Removed CEO/CTO fields from startups table")
        except Exception as e:
            print(f"Error removing fields from startups: {e}")
            conn.rollback()

        # Remove from invalid_startups table
        try:
            conn.execute(text("ALTER TABLE invalid_startups DROP COLUMN IF EXISTS ceo_name CASCADE"))
            conn.execute(text("ALTER TABLE invalid_startups DROP COLUMN IF EXISTS ceo_linkedin CASCADE"))
            conn.execute(text("ALTER TABLE invalid_startups DROP COLUMN IF EXISTS cto_name CASCADE"))
            conn.execute(text("ALTER TABLE invalid_startups DROP COLUMN IF EXISTS cto_linkedin CASCADE"))
            conn.commit()
            print("Removed CEO/CTO fields from invalid_startups table")
        except Exception as e:
            print(f"Error removing fields from invalid_startups: {e}")
            conn.rollback()

if __name__ == "__main__":
    remove_ceo_cto_fields()
    print("Migration completed!")