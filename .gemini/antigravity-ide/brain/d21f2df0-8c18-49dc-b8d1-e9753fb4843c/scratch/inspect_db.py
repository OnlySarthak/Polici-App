import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("ASYNC_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/insurance_db")
print("Connecting async to:", DATABASE_URL)

async def main():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # Run inspector in sync context using conn.run_sync
        def inspect_sync(connection):
            inspector = inspect(connection)
            for table_name in inspector.get_table_names():
                print(f"\nTable: {table_name}")
                for column in inspector.get_columns(table_name):
                    print(f" - {column['name']}: {column['type']} (nullable={column['nullable']})")
        
        await conn.run_sync(inspect_sync)

if __name__ == "__main__":
    asyncio.run(main())
