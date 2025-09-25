"""
Drop unused venture_capitals table from database
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nvidia_user:nvidia_pass@localhost:5432/nvidia_inception_db"
)

def drop_venture_capitals_table():
    """Drop the unused venture_capitals table if it exists"""

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'venture_capitals'
                );
            """))

            table_exists = result.scalar()

            if table_exists:
                # Drop the table
                conn.execute(text("DROP TABLE IF EXISTS venture_capitals CASCADE"))
                conn.commit()
                print("Successfully dropped venture_capitals table")
            else:
                print("Table venture_capitals does not exist")

        except Exception as e:
            print(f"Error dropping venture_capitals table: {e}")
            conn.rollback()

if __name__ == "__main__":
    drop_venture_capitals_table()
    print("Migration completed!")