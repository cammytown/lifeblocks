from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lifeblocks.models import Base
from lifeblocks.services.data_service import DataService


def init_database():
    # Create database engine
    engine = create_engine("sqlite:///blocks.db")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session factory
    Session = sessionmaker(bind=engine)

    # Create session
    session = Session()

    # Initialize data service and ensure schema is current
    data_service = DataService(session)
    data_service.ensure_schema_current()

    return engine, session
