from sqlmodel import Session, create_engine

from backend.core.settings import settings

engine = create_engine(settings.DB_URI)


def db_session():
    with Session(engine) as session:
        yield session
