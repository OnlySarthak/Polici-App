from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.schemas.state import RoutingState, SqlDataRetrivalIds
from app.agents.nodes import intent_router_node, data_retrival_node, llm_response_node

# ==========================================
# ASSEMBLING THE WORKFLOW GRAPH
# ==========================================
# Create the blueprint and bind it to our lightweight State structure
builder = StateGraph(RoutingState)

# Attach our active worker nodes
builder.add_node("intent_router", intent_router_node)
builder.add_node("data_retrival", data_retrival_node)
builder.add_node("llm_response", llm_response_node)

# Map out the flow path layout connections
builder.add_edge(START, "intent_router")
builder.add_edge("intent_router", "data_retrival")
builder.add_edge("data_retrival", "llm_response")
builder.add_edge("llm_response", END)

# Compile the workflow blueprint into an executable graph engine
memory = MemorySaver()
compiled_graph = builder.compile(checkpointer=memory)

# ==========================================
# THE TEST BENCH FUNCTION
# ==========================================
async def graph_runner(state: RoutingState, userSqlDataIds: SqlDataRetrivalIds, config: dict):
    # Pass user SQL IDs to the state context
    if userSqlDataIds:
        if isinstance(userSqlDataIds, dict):
            state["user_sql_ids"] = userSqlDataIds
        else:
            state["user_sql_ids"] = userSqlDataIds.model_dump()
            
    final_output = await compiled_graph.ainvoke(state, config=config)
    return final_output
