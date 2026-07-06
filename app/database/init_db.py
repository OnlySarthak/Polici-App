import os
from sqlalchemy import create_engine, text
from app.models.insurance import Base
from dotenv import load_dotenv

load_dotenv()

def init_database():
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/insurance_db")
    print(f"Syncing database schema at: {DATABASE_URL}")
    try:
        engine = create_engine(DATABASE_URL)
        
        # Create tables if they do not exist
        Base.metadata.create_all(bind=engine)
        print("Base tables check/creation completed.")
        
        alter_queries = [
            "ALTER TABLE insurances ADD COLUMN IF NOT EXISTS vehicle_id INTEGER REFERENCES vehicles(id);",
            "ALTER TABLE policy_documents ADD COLUMN IF NOT EXISTS document_text TEXT;"
        ]
        
        with engine.connect() as conn:
            # PostgreSQL requires committing DDL changes or running outside transaction depending on config
            for query in alter_queries:
                conn.execute(text(query))
            conn.commit()
            print("Vehicle relationship column check/alteration completed successfully.")
            
    except Exception as e:
        print(f"Warning: Database schema sync failed: {e}")

if __name__ == "__main__":
    init_database()
