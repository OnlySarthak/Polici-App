from app.schemas.state import RoutingState
from fastapi import APIRouter, Cookie
from fastapi.responses import StreamingResponse
from typing import Optional

from pydantic import BaseModel, Field
from app.schemas.state import SqlDataRetrivalIds, RoutingState

from app.agents.graph import graph_runner

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.get("/")
async def get_chat(
        prompt: str, 
        session_id: str,
        user_id: Optional[int] = Cookie(None), 
        insurance_id: Optional[str] = Cookie(None), 
        application_id: Optional[str] = Cookie(None),
        vehicle_id: Optional[str] = Cookie(None)
    ):
    userSqlDataId = SqlDataRetrivalIds(
        userId=user_id,
        insuranceId=insurance_id,
        applicationId=application_id,
        vehicleId=vehicle_id
    )
    
    # Create the config payload containing the thread ID (for LangGraph Checkpointer)
    config = {"configurable": {"thread_id": session_id}}
    
    # Instantiate short-lived RoutingState (Historical data is auto-injected by Checkpointer)
    state: RoutingState = {
        "last_user_input": prompt,
        "vector_output": None,
        "sql_output": None,
        "web_output": None,
        "chat_history": [],
        "routing_payload": None,
        "user_sql_ids": None,
    }
    
    result = await graph_runner(state, userSqlDataId, config)
    assistant_response = ""
    if result and result.get("chat_history"):
        assistant_response = result["chat_history"][-1].get("assistant", "")
    return {"response": assistant_response}

@router.get("/refresh")
async def clear_chat():
    global state
    state = {
        "last_user_input": None,
        "vector_output": None,
        "sql_output": None,
        "web_output": None,
        "chat_history": [],
        "routing_payload": None,
        "user_sql_ids": None,
    }
