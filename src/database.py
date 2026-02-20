# database.py
from sqlmodel import SQLModel, Session, create_engine
from .config import settings
from .model import User, Home, Leadership, News, Gallary, Contact, AuditLog, HeroSlide
import time

engine = create_engine(settings.DATABASE_URL, echo=True)

def create_db_and_tables(retries=5, delay=3):
    """
    Create tables, retry if DB isn't ready yet.
    Useful for container deployments.
    """
    for attempt in range(retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("Database tables created successfully!")
            return
        except Exception as e:
            print(f"DB connection failed: {e}, retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Failed to connect to DB after multiple retries")

def get_session() -> Session:
    with Session(engine) as session:
        yield session