import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/insurance_db")
engine = create_engine(DATABASE_URL,pool_pre_ping=True)

def SessionLocal():

    # 2. Define a factory blueprint for creating individual local sessions
    # (We turn off autocommit so that changes only save when we explicitly ask)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return SessionLocal

