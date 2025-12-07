from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional


# ==========
# Request/Response models for user query
# ==========

class QueryRequest(BaseModel):
    user_query: str
    routing_mode: str = "auto" # auto or manual
    selected_agent: Optional[str] = None # used if routing_mode is "manual"




class QueryResponse(BaseModel):
    reply: str


# ==========
# Agent Registry models (Segment 2)
# ==========

class AgentInfo(BaseModel):
    agent_name: str
    description: str
    capability_tags: List[str]
    curated_routing_prompts: str
    example_queries: List[str]
    usage_hints: Optional[str] = None
    how_to_call: str
    version: Optional[str] = None
    health_status: str  # e.g. "healthy", "unhealthy", "unknown"


class AgentsListResponse(BaseModel):
    agents: List[AgentInfo]


# In-memory registry (very simple for now)
AGENT_REGISTRY: Dict[str, AgentInfo] = {}


def register_builtin_dummy_agent() -> None:
    """
    Segment 2:
    - Register a single DummyAgent in the in-memory registry.
    - This is just data; we are NOT calling the agent yet.
    """
    dummy = AgentInfo(
        agent_name="DummyAgent",
        description="A simple built-in agent used for testing the AgentHost registry.",
        capability_tags=["test", "dummy", "echo"],
        curated_routing_prompts=(
            "Select this agent only for testing or echo-style queries. "
            "It does not perform any real work and is used to validate the AgentHost pipeline."
        ),
        example_queries=[
            "Test if AgentHost can see this agent.",
            "Echo my message using DummyAgent.",
        ],
        usage_hints=(
            "Responses from this agent are only for debugging and should not be treated as real results."
        ),
        how_to_call="internal://dummy",  # placeholder, real call wiring comes later
        version="v0.0.1",
        health_status="healthy",
    )
    AGENT_REGISTRY[dummy.agent_name] = dummy
# ==========
# DummyAgent implementation (Segment 3)
# ==========
def dummy_agent_handle(user_query: str) -> str:
    """
    Very simple implementation for DummyAgent.
    For now, it just echoes the user's query.
    Later, real agents will do MCP/RAG/API work.
    """
    return f"DummyAgent got your query: {user_query}"


# Mapping of agent_name -> handler function
AGENT_HANDLERS = {
    "DummyAgent": dummy_agent_handle,
}
# ==========
# FastAPI app
# ==========

app = FastAPI(
    title="AgentHost MVP",
    version="0.0.4",
    description=(
        "AgentHost with in-memory agent registry, a simple DummyAgent, "
        "and basic routing_mode support (auto/manual). No LLM routing yet."
    ),
)

# ==========
# app startup
# ==========

@app.on_event("startup")
async def startup_event() -> None:
    """
    On startup, register a built-in DummyAgent into the registry.
    """
    register_builtin_dummy_agent()


@app.post("/agenthost/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest) -> QueryResponse:
    """
    Segment 4:
    - Accept routing_mode: 'auto' or 'manual'.
    - If manual: use payload.selected_agent (must exist in registry and handlers).
    - If auto: for now, always use DummyAgent (LLM router will come later).
    """

    # Decide which agent to use
    if payload.routing_mode == "manual":
        # Manual mode: user must specify selected_agent
        if not payload.selected_agent:
            return QueryResponse(
                reply=(
                    "AgentHost error: routing_mode='manual' requires 'selected_agent' "
                    "to be provided."
                )
            )
        agent_name = payload.selected_agent
    else:
        # Auto mode (or any other) – for now always DummyAgent
        agent_name = "DummyAgent"
    # Look up agent in registry and handler mapping
    agent_info = AGENT_REGISTRY.get(agent_name)
    handler = AGENT_HANDLERS.get(agent_name)

    if agent_info is None or handler is None:
        return QueryResponse(
            reply=(
                f"AgentHost error: selected agent '{agent_name}' "
                "is not available in registry/handlers."
            )
        )

    # Call the agent handler
    agent_reply = handler(payload.user_query)

    return QueryResponse(reply=agent_reply)

@app.get("/agenthost/agents", response_model=AgentsListResponse)
async def list_agents() -> AgentsListResponse:
    """
    Segment 2:
    - Expose the in-memory registry so we can see which agents are registered.
    - Currently returns a single built-in DummyAgent.
    """
    agents = list(AGENT_REGISTRY.values())
    return AgentsListResponse(agents=agents)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=8000)
