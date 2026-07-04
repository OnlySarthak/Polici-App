from typing import Any, Dict, List, TypedDict,Optional
from pydantic import BaseModel, Field

# ==========================================
# 1. THE STATE CLIPBOARD (LangGraph TypedDict)
# ==========================================
class RoutingState(TypedDict):
    vector_output : object | None
    sql_output : object | None
    web_output : object | None
    chat_history : List[object] 
    last_user_input : str
    routing_payload: Optional[dict]
    user_sql_ids: Optional[dict]
    
# =====================================================================
# 1. ROUTER STRUCTURE CONTRACTS (Intent Analysis Outputs)
# =====================================================================
class IntentRoutingPayload(BaseModel):
    requires_vector: bool = Field(description="True if the query needs semantic policy rules text from the knowledge base.")
    requires_structure: bool = Field(description="True if the query asks about real-time user profiles, active applications, or status limits.")
    requires_web_search: bool = Field(description="True if the query asks general knowledge, public regulations, news, or topics requiring public internet search.")
    
    # Target-specific search strings
    vector_search_query: Optional[str] = Field(default=None, description="Refined semantic query text for ChromaDB lookup.")
    sql_user_query: Optional[str] = Field(default=None, description="Optimized Postgres SQL filtering parameters for the user table.")
    sql_insurance_query: Optional[str] = Field(default=None, description="Optimized Postgres SQL filtering parameters for the insurance table.")
    sql_application_query: Optional[str] = Field(default=None, description="Optimized Postgres SQL filtering parameters for the applications table.")
    web_search_query: Optional[str] = Field(default=None, description="Refined search query text for DuckDuckGo web search. Ensure no customer name, email, internal IDs, or company secrets are present here.")

class SqlDataRetrivalIds(BaseModel):
    userId : Optional[int]
    insuranceId : Optional[str]
    applicationId : Optional[str]