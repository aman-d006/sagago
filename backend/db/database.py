from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from core.config import settings

engine = create_engine(
    settings.DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

    try:
        with engine.begin() as conn:
            result = conn.execute(text("PRAGMA table_info('story_jobs')"))
            cols = [row[1] for row in result.fetchall()]
            if 'completed_at' not in cols:
                conn.execute(text("ALTER TABLE story_jobs ADD COLUMN completed_at DATETIME"))
    except Exception:
        pass