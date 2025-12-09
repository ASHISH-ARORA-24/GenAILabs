from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import httpx
import os
import uuid


# ==========
# LiteLLM configuration (for router + composer)
# ==========

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4100")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-litellm-hub-local-123")

# For routing, use a small, cheap model
ROUTER_MODEL_NAME = os.getenv("ROUTER_MODEL_NAME", "tinyllama")

# For composing final answers, you can use a slightly better model
COMPOSER_MODEL_NAME = os.getenv("COMPOSER_MODEL_NAME", "qwen2.5")


# ==========
# Request/Response models for user query (Streamlit ↔ AgentHost)
# ==========

class QueryRequest(BaseModel):
    user_query: str
    routing_mode: str = "auto"              # "auto" or "manual"
    selected_agent: Optional[str] = None    # used only when routing_mode = "manual"


class QueryResponse(BaseModel):
    reply: str


# ==========
# Execution Contract models (AgentHost ↔ Agents)
# ==========

class ExecutionRequest(BaseModel):
    request_id: str
    user_query: str
    routing_mode: str
    selected_agent: str
    # later: session_context, parsed_parameters, agent_instructions, etc.


class ExecutionResponse(BaseModel):
    request_id: str
    status: str                 # "success" | "error" | "partial"
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ==========
# Agent Registry models
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


# In-memory registry
AGENT_REGISTRY: Dict[str, AgentInfo] = {}


def register_builtin_dummy_agent() -> None:
    """
    Register a single DummyAgent in the in-memory registry.
    This is just data; routing and execution are wired separately.
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
        how_to_call="internal://dummy",
        version="v0.0.1",
        health_status="healthy",
    )
    AGENT_REGISTRY[dummy.agent_name] = dummy


# ==========
# DummyAgent implementation (uses ExecutionRequest/ExecutionResponse)
# ==========

def dummy_agent_handle(exec_request: ExecutionRequest) -> ExecutionResponse:
    """
    Very simple implementation for DummyAgent.

    - Accepts a structured ExecutionRequest.
    - Returns an ExecutionResponse with status 'success'.
    - result is just an echo string for now.
    """

    echo_text = f"DummyAgent got your query: {exec_request.user_query}"

    return ExecutionResponse(
        request_id=exec_request.request_id,
        status="success",
        result=echo_text,
        error=None,
        metadata={
            "agent": "DummyAgent",
            "routing_mode": exec_request.routing_mode,
        },
    )


# Mapping of agent_name -> handler function (ExecutionRequest -> ExecutionResponse)
AGENT_HANDLERS = {
    "DummyAgent": dummy_agent_handle,
}


# ==========
# LLM Agent Selection helper (Router)
# ==========

def select_agent_with_llm(user_query: str, agents: List[AgentInfo]) -> Optional[str]:
    """
    Use LiteLLM to decide which agent should handle the query.

    - Sends user_query + detailed agent metadata:
        * agent_name
        * description
        * capability_tags
        * curated_routing_prompts
        * example_queries
    - Asks the LLM to pick the single best agent.
    - Tries to match the LLM output against known agent names.
    - On any error or mismatch, returns None so AgentHost can fallback.
    """

    if not agents:
        return None

    # Build a rich textual description of agents using all the routing metadata
    agents_text_lines = []
    for agent in agents:
        lines = [
            f"Agent Name: {agent.agent_name}",
            f"Description: {agent.description}",
            f"Tags: {', '.join(agent.capability_tags) if agent.capability_tags else 'None'}",
            f"When to use: {agent.curated_routing_prompts}",
        ]
        if agent.example_queries:
            lines.append("Example queries:")
            for ex in agent.example_queries[:3]:
                lines.append(f"  - {ex}")
        agents_text_lines.append("\n".join(lines))

    agents_text = "\n\n".join(agents_text_lines)

    system_message = (
        "You are an agent router.\n"
        "You are given a user query and a list of available agents with their descriptions, "
        "tags, routing hints, and example queries.\n"
        "Your job is to choose the single best agent to handle the query.\n"
        "You must reply with ONLY the agent_name as plain text (for example: DummyAgent).\n"
        "If no agent is appropriate, reply with: none"
    )

    user_message = (
        f"User query:\n{user_query}\n\n"
        f"Available agents:\n{agents_text}\n\n"
        "Based on the descriptions, tags, routing hints, and example queries above, "
        "which agent should handle this query?\n"
        "Remember: reply with only the agent_name or 'none'."
    )

    payload = {
        "model": ROUTER_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 32,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{LITELLM_BASE_URL}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                },
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()

        raw_content = data["choices"][0]["message"]["content"]
        if not raw_content:
            return None

        content = raw_content.strip()
        lower = content.lower()

        # 1) If it clearly says 'none'
        if "none" in lower:
            return None

        # 2) Try to match against known agent names (case-insensitive containment)
        for agent in agents:
            name_lower = agent.agent_name.lower()
            if name_lower in lower:
                return agent.agent_name

        # 3) Try first token exact match
        first_token = content.split()[0].strip()
        for agent in agents:
            if first_token == agent.agent_name:
                return agent.agent_name

        # 4) If nothing matched, return None so AgentHost can fallback
        print(f"[select_agent_with_llm] Could not match router output to any agent. Raw: {raw_content!r}")
        return None

    except Exception as e:
        print(f"[select_agent_with_llm] Error calling LiteLLM (router): {e}")
        return None


# ==========
# LLM Composer helper (Final answer formatting)  [Segment 8]
# ==========

def compose_final_answer_with_llm(
    user_query: str,
    agent_name: str,
    agent_info: AgentInfo,
    exec_response: ExecutionResponse,
) -> str:
    """
    Use LiteLLM to turn ExecutionResponse + context into a user-friendly final answer.

    - If status = success: explain result in clear language.
    - If status = error: explain the error politely.
    - If status = partial (future): explain what was done and what is missing.

    On any LLM error, falls back to a simple non-LLM answer.
    """

    status = exec_response.status
    raw_result = exec_response.result
    error_text = exec_response.error

    # Fallback string builder (used if LLM fails)
    def build_fallback() -> str:
        if status != "success":
            return (
                f"Agent '{agent_name}' could not complete the request. "
                f"Status: {status}. Details: {error_text or 'Unknown error.'}"
            )
        return str(raw_result) if raw_result is not None else ""

    # Prepare context for LLM
    result_str = str(raw_result) if raw_result is not None else "None"
    metadata_str = str(exec_response.metadata) if exec_response.metadata is not None else "None"
    usage_hints = agent_info.usage_hints or ""

    system_message = (
        "You are a helpful assistant that formats responses for end users.\n"
        "You will be given:\n"
        "- The original user query\n"
        "- The name and description of the agent that ran\n"
        "- The agent's execution status and raw result or error\n"
        "- Optional usage hints describing how to present the answer\n\n"
        "Your job is to produce a clear, user-friendly answer.\n"
        "If there was an error, explain it briefly and politely.\n"
        "Do not invent data that is not present in the result.\n"
    )

    user_message = (
        f"User query:\n{user_query}\n\n"
        f"Agent used: {agent_name}\n"
        f"Agent description: {agent_info.description}\n\n"
        f"Agent usage hints (if any): {usage_hints}\n\n"
        f"Execution status: {status}\n"
        f"Execution result (raw): {result_str}\n"
        f"Execution error (if any): {error_text or 'None'}\n"
        f"Execution metadata: {metadata_str}\n\n"
        "Please produce a final answer for the user.\n"
        "- If status is 'success', answer the query using the result.\n"
        "- If status is 'error', explain what went wrong in simple terms.\n"
        "- Keep the tone clear and concise."
    )

    payload = {
        "model": COMPOSER_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 256,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{LITELLM_BASE_URL}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                },
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()

        raw_content = data["choices"][0]["message"]["content"]
        if not raw_content:
            return build_fallback()

        return raw_content.strip()

    except Exception as e:
        print(f"[compose_final_answer_with_llm] Error calling LiteLLM (composer): {e}")
        return build_fallback()


# ==========
# FastAPI app
# ==========

app = FastAPI(
    title="AgentHost MVP",
    version="0.0.8",
    description=(
        "AgentHost with in-memory agent registry, a simple DummyAgent, "
        "routing_mode support (auto/manual), an LLM-based agent selector via LiteLLM, "
        "a structured ExecutionRequest/ExecutionResponse contract, and an LLM-based "
        "final response composer."
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
    Handle user queries:

    - routing_mode = 'manual':
        * Uses payload.selected_agent (must exist in registry & handlers).
        * Does NOT call the LLM router.
    - routing_mode = 'auto' (default):
        * Calls the LLM-based selector to choose an agent.
        * If selector fails or returns 'none', falls back to DummyAgent.

    Then:
    - Builds an ExecutionRequest
    - Invokes the agent handler
    - Sends ExecutionResponse + context to the Composer LLM
    - Returns the composed final answer to the caller.
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
        # Auto mode: use LLM router to decide
        agents_list = list(AGENT_REGISTRY.values())
        routed_agent = select_agent_with_llm(payload.user_query, agents_list)

        if not routed_agent or routed_agent.lower() == "none":
            # Fallback behaviour for now: use DummyAgent
            agent_name = "DummyAgent"
        else:
            agent_name = routed_agent

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

    # Build ExecutionRequest
    request_id = str(uuid.uuid4())
    exec_request = ExecutionRequest(
        request_id=request_id,
        user_query=payload.user_query,
        routing_mode=payload.routing_mode,
        selected_agent=agent_name,
    )

    # Call the agent handler safely
    try:
        exec_response = handler(exec_request)
    except Exception as e:
        # If agent itself throws, wrap as ExecutionResponse error
        exec_response = ExecutionResponse(
            request_id=request_id,
            status="error",
            result=None,
            error=f"Agent '{agent_name}' raised an exception: {e}",
            metadata={"agent": agent_name},
        )

    # Use Composer LLM to turn ExecutionResponse into final user answer
    final_answer = compose_final_answer_with_llm(
        user_query=payload.user_query,
        agent_name=agent_name,
        agent_info=agent_info,
        exec_response=exec_response,
    )

    return QueryResponse(reply=final_answer)


@app.get("/agenthost/agents", response_model=AgentsListResponse)
async def list_agents() -> AgentsListResponse:
    """
    Expose the in-memory registry so we can see which agents are registered.
    Currently returns a single built-in DummyAgent.
    """
    agents = list(AGENT_REGISTRY.values())
    return AgentsListResponse(agents=agents)


@app.get("/agenthost/agents", response_model=AgentsListResponse)
async def list_agents() -> AgentsListResponse:
    """
    Expose the in-memory registry so we can see which agents are registered.
    Currently returns a single built-in DummyAgent.
    """
    agents = list(AGENT_REGISTRY.values())
    return AgentsListResponse(agents=agents)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=8000)