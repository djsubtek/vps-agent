import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database():
    Base.metadata.create_all(bind=engine)

    statements = [
        "ALTER TABLE items ALTER COLUMN title DROP NOT NULL",
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'items' AND column_name = 'content'
            ) THEN
                ALTER TABLE items ALTER COLUMN content DROP NOT NULL;
            END IF;
        END $$;
        """,
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS source TEXT",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS content_type TEXT NOT NULL DEFAULT 'text'",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS raw_content TEXT",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS extracted_text TEXT",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS summary TEXT",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS category TEXT",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS tags JSONB",
        "ALTER TABLE items ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'new'",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
