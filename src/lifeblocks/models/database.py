from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lifeblocks.models import Base


def init_database():
    # Create database engine
    engine = create_engine("sqlite:///blocks.db")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session factory
    Session = sessionmaker(bind=engine)

    # Create session
    session = Session()

    return engine, session
