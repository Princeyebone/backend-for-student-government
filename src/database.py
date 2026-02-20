from sqlmodel import SQLModel, Session, create_engine
from .config import settings
# Import all models so SQLModel can discover them
from .model import User, Home, Leadership, News, Gallary, Contact, AuditLog, HeroSlide

engine = create_engine(settings.DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    with Session(engine) as session:
        yield session