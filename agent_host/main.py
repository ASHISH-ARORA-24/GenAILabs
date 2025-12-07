from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional


# ==========
# Request/Response models for user query
# ==========

class QueryRequest(BaseModel):
    user_query: str


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
# FastAPI app
# ==========

app = FastAPI(
    title="AgentHost MVP",
    version="0.0.2",
    description=(
        "Minimal skeleton for AgentHost with an in-memory agent registry. "
        "No routing or real agent execution yet."
    ),
)


@app.on_event("startup")
async def startup_event() -> None:
    """
    On startup, register a built-in DummyAgent into the registry.
    """
    register_builtin_dummy_agent()


@app.post("/agenthost/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest) -> QueryResponse:
    """
    Segment 1:
    - Just confirm that AgentHost receives queries.
    - Still: No LLM, no routing, no agents being executed.
    """
    return QueryResponse(reply=f"AgentHost received your query: {payload.user_query}")


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
