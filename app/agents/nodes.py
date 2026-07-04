import os
import re
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from app.schemas.state import RoutingState, IntentRoutingPayload
from app.utils.constants import INTENSION_PROMPT, FINAL_LLM_PROMPT
from app.services.data_retrieval import (
    AsyncSessionLocal, 
    get_vector_data, 
    fetch_user_profile, 
    fetch_application_details, 
    fetch_insurance_details,
    get_web_data
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

#extract id from the sql query using regex
def extract_id(query_str: Optional[str]) -> Optional[str]:
    if not query_str:
        return None
    # Look for value after equals sign (e.g., = 1, = 'abc', = "abc")
    match = re.search(r"=\s*['\"]?([a-zA-Z0-9_-]+)['\"]?", query_str)
    if match:
        return match.group(1)
    # If the whole string is alphanumeric, return it
    clean = query_str.strip()
    if clean.isalnum():
        return clean
    return None

# ==========================================
# THE GRAPH NODE WORKERS (LangChain Orchestration)
# ==========================================
async def intent_router_node(state: RoutingState) -> dict:
    print("🧠 --- Node Processing: Running Database Directives Prompt ---")
    
    user_input = state["last_user_input"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    
    # Expand the system prompt with exact architecture constraints
    system_prompt_layout = ChatPromptTemplate.from_messages([
        ("system", INTENSION_PROMPT),
        ("user", "{user_input}")        #here we are just telling the llm to classify the user input, not passing actual values
    ])
    # convert the llm response into pydantic model
    structured_llm = llm.with_structured_output(IntentRoutingPayload)

                #  user prompt , sys instruction | output structure
    intelligent_pipeline = system_prompt_layout | structured_llm
    
    pydantic_response: IntentRoutingPayload = await intelligent_pipeline.ainvoke({
        "user_input": user_input 
    }) 
    
    return {"routing_payload": pydantic_response.model_dump()}

async def data_retrival_node(state: RoutingState) -> dict:
    print("🧠 --- Node Processing: Running Data Retrieval ---")
    routing_payload_dict = state.get("routing_payload")
    if not routing_payload_dict:
        return {"vector_output": None, "sql_output": None, "web_output": None}
    
    intent_output = IntentRoutingPayload(**routing_payload_dict)
    vector_output = None
    sql_output = []
    web_output = None
    
    # Vector data retrieval
    if intent_output.requires_vector:
        vector_output = get_vector_data(intent_output.vector_search_query)
    
    # SQL data retrieval
    if intent_output.requires_structure:
        user_query = intent_output.sql_user_query
        application_query = intent_output.sql_application_query
        insurance_query = intent_output.sql_insurance_query
 
        # Get explicit IDs passed in state
        user_sql_ids = state.get("user_sql_ids") or {}

        async with AsyncSessionLocal() as session:
            if user_query:
                user_id = user_sql_ids.get("userId")
                if user_id is None:
                    extracted = extract_id(user_query)
                    if extracted and extracted.isdigit():
                        user_id = int(extracted)
                if user_id is not None:
                    user_output = await fetch_user_profile(session, user_id, user_query)
                    sql_output.append(user_output)
            if insurance_query:
                insurance_id = user_sql_ids.get("insuranceId")
                if not insurance_id:
                    extracted = extract_id(insurance_query)
                    if extracted:
                        insurance_id = extracted
                if insurance_id:
                    insurance_output = await fetch_insurance_details(session, insurance_id)
                    sql_output.append(insurance_output)
            if application_query:
                application_id = user_sql_ids.get("applicationId")
                if not application_id:
                    extracted = extract_id(application_query)
                    if extracted:
                        application_id = extracted
                if application_id:
                    application_output = await fetch_application_details(session, application_id)
                    sql_output.append(application_output)

    # Web search retrieval
    if intent_output.requires_web_search:
        web_output = get_web_data(intent_output.web_search_query)

    return {"vector_output": vector_output, "sql_output": sql_output, "web_output": web_output}

async def llm_response_node(state: RoutingState) -> dict:
    print("🧠 --- Node Processing: Running LLM Synthesis Response ---")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    user_input = state["last_user_input"]
    
    # Formatting context data from SQL, vector db, and web search outputs
    context_data = f"SQL DB Output:\n{state.get('sql_output')}\n\nVector DB Output:\n{state.get('vector_output')}\n\nWeb Search Output:\n{state.get('web_output')}"
    
    # Concrete system prompt explaining multi-database structural targets
    system_prompt_layout = ChatPromptTemplate.from_messages([
        ("system", FINAL_LLM_PROMPT)
    ])
    
    # Bind the model and string parser
    intelligent_pipeline = system_prompt_layout | llm | StrOutputParser()
    
    # Invoke using your explicit dictionary keys formatted into the prompt
    pydantic_response: str = await intelligent_pipeline.ainvoke({
        "context_data": context_data,
        "user_query": user_input
    })

    chat_history = list(state.get("chat_history") or [])
    chat_history.append({
        "user": user_input,
        "assistant": pydantic_response
    })
    
    return {"chat_history": chat_history}
