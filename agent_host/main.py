from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import httpx
import os
import uuid
import logging
from logging.handlers import RotatingFileHandler


# ============================================================
# LOGGING (Console + File Rotating Logs)
# ============================================================

os.makedirs("logs", exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

file_handler = RotatingFileHandler(
    "logs/agenthost.log",
    maxBytes=5_000_000,   # 5MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

logger = logging.getLogger("agenthost")
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)


# ============================================================
# LITELLM CONFIG
# ============================================================

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:4100")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "sk-litellm-hub-local-123")

ROUTER_MODEL_NAME = os.getenv("ROUTER_MODEL_NAME", "tinyllama")
COMPOSER_MODEL_NAME = os.getenv("COMPOSER_MODEL_NAME", "qwen2.5")  # also used for fallback chat


# ============================================================
# MODELS: UI ↔ AgentHost
# ============================================================

class QueryRequest(BaseModel):
    user_query: str
    routing_mode: str = "auto"            # auto/manual
    selected_agent: Optional[str] = None  # only used in manual mode


class QueryResponse(BaseModel):
    reply: str


# ============================================================
# MODELS: AgentHost ↔ Agents (Execution Contract)
# ============================================================

class ExecutionRequest(BaseModel):
    request_id: str
    user_query: str
    routing_mode: str
    selected_agent: str


class ExecutionResponse(BaseModel):
    request_id: str
    status: str                     # success/error/partial
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================
# AGENT REGISTRY MODELS
# ============================================================

class AgentInfo(BaseModel):
    agent_name: str
    description: str
    capability_tags: List[str]
    curated_routing_prompts: str
    example_queries: List[str]
    usage_hints: Optional[str] = None
    how_to_call: str
    version: Optional[str] = None
    health_status: str


class AgentsListResponse(BaseModel):
    agents: List[AgentInfo]


# Used for Register API
class AgentRegisterRequest(BaseModel):
    agent_name: str
    description: str
    capability_tags: List[str] = []
    curated_routing_prompts: str = ""
    example_queries: List[str] = []
    usage_hints: Optional[str] = None
    how_to_call: str
    version: Optional[str] = None
    health_status: str = "healthy"


# Used for Deregister API
class AgentDeregisterRequest(BaseModel):
    agent_name: str


AGENT_REGISTRY: Dict[str, AgentInfo] = {}


# ============================================================
# REGISTER BUILT-IN DUMMY AGENT
# ============================================================

def register_builtin_dummy_agent():
    dummy = AgentInfo(
        agent_name="DummyAgent",
        description="A simple built-in agent used for testing the AgentHost pipeline.",
        capability_tags=["test", "echo", "dummy"],
        curated_routing_prompts="Use this agent only for basic testing or echo responses.",
        example_queries=["test agent", "echo this", "hello"],
        usage_hints="This agent only echoes back.",
        how_to_call="internal://dummy",
        version="v1",
        health_status="healthy",
    )
    AGENT_REGISTRY[dummy.agent_name] = dummy


# ============================================================
# DUMMY AGENT IMPLEMENTATION
# ============================================================

def dummy_agent_handle(exec_request: ExecutionRequest) -> ExecutionResponse:
    echo = f"DummyAgent got your query: {exec_request.user_query}"
    return ExecutionResponse(
        request_id=exec_request.request_id,
        status="success",
        result=echo,
        error=None,
        metadata={"agent": "DummyAgent"},
    )


AGENT_HANDLERS = {
    "DummyAgent": dummy_agent_handle
}


# ============================================================
# ROUTER LLM - Select Agent
# ============================================================

def select_agent_with_llm(user_query: str, agents: List[AgentInfo]) -> Optional[str]:
    if not agents:
        logger.warning("[router] No agents registered (or none eligible).")
        return None

    # Build agents description block
    agents_text = ""
    for a in agents:
        agents_text += (
            f"Agent Name: {a.agent_name}\n"
            f"Description: {a.description}\n"
            f"Tags: {', '.join(a.capability_tags)}\n"
            f"When to use: {a.curated_routing_prompts}\n"
            f"Example queries: {a.example_queries[:3]}\n\n"
        )

    system_message = (
        "You are an agent router. Pick ONE agent.\n"
        "Reply ONLY with the agent name or 'none'."
    )

    user_message = (
        f"User query:\n{user_query}\n\n"
        f"Available agents:\n{agents_text}"
    )

    payload = {
        "model": ROUTER_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 32,
    }

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{LITELLM_BASE_URL}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            )
        resp.raise_for_status()
        out = resp.json()["choices"][0]["message"]["content"].strip()

        if out.lower() == "none":
            logger.info("[router] LLM selected none.")
            return None

        for a in agents:
            if a.agent_name.lower() in out.lower():
                logger.info("[router] LLM selected agent: %s", a.agent_name)
                return a.agent_name

        logger.warning("[router] No valid match for LLM output: %r", out)
        return None

    except Exception as e:
        logger.error("[router] Error calling router LLM: %s", e)
        return None


# ============================================================
# FALLBACK CHAT (When no agent can be used)
# ============================================================

def fallback_chat_llm(user_query: str) -> str:
    system_message = "You are a helpful assistant. Answer the user's question directly."

    payload = {
        "model": COMPOSER_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ],
        "max_tokens": 256
    }

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.post(
                f"{LITELLM_BASE_URL}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            )
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"]
        return result.strip()

    except Exception as e:
        logger.error("[fallback_chat] Error calling chat fallback: %s", e)
        return "AgentHost is not capable of handling this request right now."


# ============================================================
# COMPOSER LLM (Final Answer Formatting)
# ============================================================

def compose_final_answer_with_llm(
    user_query: str,
    agent_name: str,
    agent_info: AgentInfo,
    exec_res: ExecutionResponse,
) -> str:

    def fallback() -> str:
        if exec_res.status != "success":
            return f"Agent '{agent_name}' failed: {exec_res.error}"
        return str(exec_res.result)

    try:
        system_msg = (
            "You are a response formatter. Use the agent result to answer the user clearly.\n"
            "If error: explain politely. Do not invent extra details."
        )

        user_msg = (
            f"User query: {user_query}\n"
            f"Agent used: {agent_name}\n"
            f"Agent description: {agent_info.description}\n"
            f"Execution status: {exec_res.status}\n"
            f"Raw result: {exec_res.result}\n"
            f"Error: {exec_res.error}\n"
        )

        payload = {
            "model": COMPOSER_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 200
        }

        with httpx.Client(timeout=20) as client:
            resp = client.post(
                f"{LITELLM_BASE_URL}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return content.strip()

    except Exception as e:
        logger.error("[composer] LLM composer failed: %s", e)
        return fallback()


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="AgentHost MVP", version="1.2")


@app.on_event("startup")
async def startup():
    register_builtin_dummy_agent()
    logger.info("AgentHost started with agents: %s", list(AGENT_REGISTRY.keys()))


# ============================================================
# CORE QUERY ENDPOINT
# ============================================================

@app.post("/agenthost/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest):

    logger.info(
        "Incoming query | routing_mode=%s | selected_agent=%s | query=%r",
        payload.routing_mode,
        payload.selected_agent,
        payload.user_query,
    )

    # ----------------------
    # Routing Mode: MANUAL
    # ----------------------
    if payload.routing_mode == "manual":
        if not payload.selected_agent:
            logger.warning("Manual mode but no selected_agent → fallback chat.")
            return QueryResponse(reply=fallback_chat_llm(payload.user_query))

        agent_name = payload.selected_agent

    else:
        # ----------------------
        # Routing Mode: AUTO
        # ----------------------
        # only consider agents that have handlers AND are healthy
        all_infos = AGENT_REGISTRY.items()
        eligible_agents: List[AgentInfo] = [
            info for name, info in all_infos
            if name in AGENT_HANDLERS and info.health_status == "healthy"
        ]

        if not eligible_agents:
            logger.warning("No eligible agents (with handlers & healthy) → fallback chat.")
            return QueryResponse(reply=fallback_chat_llm(payload.user_query))

        agent_name = select_agent_with_llm(payload.user_query, eligible_agents)

        if not agent_name:
            logger.info("Router returned NONE → fallback chat.")
            return QueryResponse(reply=fallback_chat_llm(payload.user_query))

    # ----------------------
    # Validate agent
    # ----------------------
    agent_info = AGENT_REGISTRY.get(agent_name)
    handler = AGENT_HANDLERS.get(agent_name)

    if not agent_info or not handler:
        logger.warning("Invalid or unhandled agent '%s' → fallback chat.", agent_name)
        return QueryResponse(reply=fallback_chat_llm(payload.user_query))

    if agent_info.health_status != "healthy":
        logger.warning("Agent unhealthy '%s' → fallback chat.", agent_name)
        return QueryResponse(reply=fallback_chat_llm(payload.user_query))

    logger.info("Using agent: %s", agent_name)

    # ----------------------
    # Build ExecutionRequest
    # ----------------------
    request_id = str(uuid.uuid4())
    exec_req = ExecutionRequest(
        request_id=request_id,
        user_query=payload.user_query,
        routing_mode=payload.routing_mode,
        selected_agent=agent_name,
    )

    # ----------------------
    # Execute Agent
    # ----------------------
    try:
        exec_res = handler(exec_req)
    except Exception as e:
        logger.error("Agent '%s' threw exception: %s", agent_name, e)
        exec_res = ExecutionResponse(
            request_id=request_id,
            status="error",
            error=str(e),
            result=None,
            metadata={"agent": agent_name},
        )

    logger.info(
        "Agent executed | request_id=%s | agent=%s | status=%s",
        exec_res.request_id,
        agent_name,
        exec_res.status,
    )

    # ----------------------
    # Compose Final Answer
    # ----------------------
    final = compose_final_answer_with_llm(
        payload.user_query, agent_name, agent_info, exec_res
    )

    logger.info(
        "Composer finished | request_id=%s | agent=%s | status=%s",
        exec_res.request_id,
        agent_name,
        exec_res.status,
    )

    return QueryResponse(reply=final)


# ============================================================
# REGISTRY ENDPOINTS (List / Register / Deregister)
# ============================================================

@app.get("/agenthost/agents", response_model=AgentsListResponse)
async def list_agents():
    """
    List all registered agents (including DummyAgent + any external agents).
    """
    return AgentsListResponse(agents=list(AGENT_REGISTRY.values()))


@app.post("/agenthost/register", response_model=AgentInfo)
async def register_agent(payload: AgentRegisterRequest):
    """
    Register or update an agent in the in-memory registry.

    NOTE:
    - Only agents that ALSO have a handler entry in AGENT_HANDLERS
      will be actually executable and considered by the router.
    - This endpoint manages metadata; execution wiring for external agents comes later.
    """
    agent = AgentInfo(**payload.model_dump())
    AGENT_REGISTRY[agent.agent_name] = agent
    logger.info("Agent registered/updated: %s", agent.agent_name)
    return agent


@app.post("/agenthost/deregister")
async def deregister_agent(payload: AgentDeregisterRequest) -> Dict[str, Any]:
    """
    Deregister an agent from the in-memory registry.

    This does NOT touch AGENT_HANDLERS (execution wiring). For now, handlers
    are managed in code. Later, for HTTP-based agents, we will add dynamic
    handler wiring as well.
    """
    name = payload.agent_name
    if name in AGENT_REGISTRY:
        del AGENT_REGISTRY[name]
        logger.info("Agent deregistered: %s", name)
        return {
            "status": "ok",
            "message": f"Agent '{name}' deregistered.",
            "agent_name": name,
        }
    else:
        logger.warning("Attempted to deregister non-existent agent: %s", name)
        return {
            "status": "not_found",
            "message": f"Agent '{name}' not found in registry.",
            "agent_name": name,
        }

@app.get("/agenthost/llm-models")
async def list_llm_models():
    """
    Fetch the available LLM models from LiteLLM.
    Returns exactly what LiteLLM returns from /v1/models.
    """
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{LITELLM_BASE_URL}/v1/models",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}"
                }
            )
        resp.raise_for_status()
        data = resp.json()
        logger.info("Fetched LLM model list from LiteLLM.")
        return data

    except Exception as e:
        logger.error("Error fetching LLM models: %s", e)
        return {
            "status": "error",
            "message": "Unable to fetch models from LiteLLM.",
            "error": str(e),
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)