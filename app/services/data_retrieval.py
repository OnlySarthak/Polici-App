import os
import re
from app.knowledge_base import kb
import asyncio
import json
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from duckduckgo_search import DDGS

from app.schemas.state import RoutingState

# Load environment variables
load_dotenv()

# =====================================================================
# 1. ASYNC POSTGRES ENGINE SETUP
# =====================================================================
DATABASE_URL = os.environ.get("ASYNC_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/insurance_db")
async_engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# =====================================================================
# 2. ASYNC DATABASE WORKER FUNCTIONS
# =====================================================================

async def fetch_user_profile(session: AsyncSession, user_id: int, user_query: Optional[str] = None):
    """Fetches the user profile data directly from the users table."""
    try:
        if user_query:
            result = await session.execute(
                text(user_query),
                {"user_id": user_id}
            )
            user = result.fetchone()
            return dict(user._mapping) if user else None
        # Fetch only necessary fields for the assistant to speed up lookup
        result = await session.execute(
            text("""
                SELECT *
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        user = result.fetchone()
        return dict(user._mapping) if user else None
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return {"error": str(e)}

async def fetch_application_details(session: AsyncSession, application_id: str):
    """Fetches the application status and metadata."""
    try:
        result = await session.execute(
            text("""
                SELECT *
                FROM applications
                WHERE application_id = :application_id
            """),
            {"application_id": application_id}
        )
        application = result.fetchone()
        return dict(application._mapping) if application else None
    except Exception as e:
        print(f"Error fetching application details: {e}")
        return {"error": str(e)}
    
async def fetch_insurance_details(session:AsyncSession,policy_id: str):
    """Fetches the insurance details directly from the insurances table."""
    try:
        result = await session.execute(
            text("""
                SELECT *
                FROM insurances
                WHERE policy_id = :policy_id
            """),
            {"policy_id": policy_id}
        )
        insurance = result.fetchone()
        return dict(insurance._mapping) if insurance else None
    except Exception as e:
        print(f"Error fetching insurance details: {e}")
        return {"error": str(e)}

async def fetch_vehicle_details(session: AsyncSession, vehicle_ref: str, vehicle_query: Optional[str] = None):
    """Fetches the vehicle details directly from the vehicles table using registration number or ID."""
    try:
        if vehicle_query:
            result = await session.execute(
                text(vehicle_query),
                {"vehicle_ref": vehicle_ref}
            )
            vehicle = result.fetchone()
            return dict(vehicle._mapping) if vehicle else None
            
        if vehicle_ref.isdigit():
            query_text = "SELECT * FROM vehicles WHERE id = :vehicle_id"
            params = {"vehicle_id": int(vehicle_ref)}
        else:
            query_text = "SELECT * FROM vehicles WHERE registration_number = :registration_number"
            params = {"registration_number": vehicle_ref}
            
        result = await session.execute(text(query_text), params)
        vehicle = result.fetchone()
        return dict(vehicle._mapping) if vehicle else None
    except Exception as e:
        print(f"Error fetching vehicle details: {e}")
        return {"error": str(e)}

def get_vector_data(query):
    try:
        if kb.retriver is None:
            kb.production_read_flow()
        output = kb.retriver.retrieve(query)
        return output
    except Exception as e:
        return {"error": str(e)}

def redact_query_pii(query: str) -> str:
    if not query:
        return query
    # 1. Redact email patterns
    query = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', query)
    # 2. Redact policy/application/user patterns (e.g. POL-123, APP-456)
    query = re.sub(r'\b(APP|POL|USR)-[\w-]+\b', '[REDACTED_ID]', query, flags=re.IGNORECASE)
    # 3. Redact digits >= 7 characters (covers phone numbers)
    query = re.sub(r'\b\+?\d{7,15}\b', '[REDACTED_PHONE]', query)
    return query

def get_web_data(query: str) -> list:
    try:
        # Scrub potentially sensitive data before sending it out
        clean_query = redact_query_pii(query)
        print(f"🌐 Querying DDG Search (Cleaned Query: '{clean_query}')...")
        
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(clean_query, max_results=3)]
            return results
    except Exception as e:
        print(f"Error during web search: {e}")
        return [{"error": str(e)}]