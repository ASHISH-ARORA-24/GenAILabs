"""
============================================================
 Agent File Service - Main Application
------------------------------------------------------------
 Handles agent registration/deregistration with AgentHost.
============================================================
"""

# =============================
# IMPORTS AND ENVIRONMENT SETUP
# =============================
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager
from typing import List

import httpx
import uvicorn
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

# ============================================================
# LOGGING SETUP (Console + Rotating File)
# ============================================================

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

# Console log handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Rotating file log handler
file_handler = RotatingFileHandler(
    "logs/agenthost.log",
    maxBytes=5_000_000,   # 5MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Main logger for this service
logger = logging.getLogger("agenthost")
logger.setLevel(logging.INFO)

# Only add handlers if they don't already exist to prevent duplicates
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
# Prevent propagation to root logger to avoid double logging
logger.propagate = False

# =============================
# CONSTANTS
# =============================
# Base URLs for dependent services
AGENTHOST_BASE_URL = os.getenv("AGENTHOST_BASE_URL", "http://localhost:8000")
MCPSERVICE_BASE_URL = os.getenv("MCPSERVICE_BASE_URL", "http://localhost:5001")

# =============================
# DATA MODELS
# =============================
# Pydantic model for agent registration payload
class AgentRegistrationModel(BaseModel):
    agent_name: str
    description: str
    capability_tags: List[str]
    curated_routing_prompts: str
    example_queries: List[str]
    usage_hints: str
    how_to_call: str
    version: str
    health_status: str

# =============================
# YAML LOADER
# =============================
# Loads agent registration details from YAML file
def load_agent_registration_yaml(path: str = "agent_registration.yaml") -> AgentRegistrationModel:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    reg_data = data["agent_registration"]
    return AgentRegistrationModel(**reg_data)

# =============================
# AGENTHOST CLIENT
# =============================
# Encapsulates all AgentHost interactions (health, register, deregister)
class AgentHost:
    def __init__(self, agent_registration_model: AgentRegistrationModel, agenthost_base_url=AGENTHOST_BASE_URL):
        self.base_url = agenthost_base_url
        self.agent_registration_model: AgentRegistrationModel = agent_registration_model

    def health_check(self):
        """Check AgentHost health endpoint."""
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "healthy":
                raise Exception("AgentHost unhealthy")
            else:
                logger.info("AgentHost is healthy")
        except Exception as e:
            logger.error(f"Error fetching health status from AgentHost: {e}")

    def deregister_agent(self):
        """Deregister agent from AgentHost."""
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.request(
                    "DELETE",
                    f"{self.base_url}/agent",
                    data=json.dumps({'agent_name': self.agent_registration_model.agent_name}),
                    headers={"Content-Type": "application/json"},
                )
            response.raise_for_status()
            logger.info("Agent deregistered successfully with AgentHost.")
            status = response.json().get("status")
            if status == "not_found":
                logger.info("Agent was not found during deregistration, proceeding to register.")
            elif status == "ok":
                logger.info("Agent deregistered successfully, proceeding to register.")
        except Exception as reg_err:
            logger.error(f"Failed to deregister agent with AgentHost: {reg_err}")

    def register_agent(self):
        """Register agent with AgentHost."""
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.base_url}/agent",
                    json=self.agent_registration_model.dict(),
                )
            response.raise_for_status()
            logger.info("Agent registered successfully with AgentHost.")
        except Exception as reg_err:
            logger.error(f"Failed to register agent with AgentHost: {reg_err}")
            raise SystemExit(f"Exiting due to AgentHost registration failure: {reg_err}")

class MCPService:
    def __init__(self, mcps_base_url=MCPSERVICE_BASE_URL):
        self.base_url = mcps_base_url
    
    def health_check(self):
        """Check MCPService health endpoint."""
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "healthy":
                raise Exception("MCPService unhealthy")
            else:
                logger.info("MCPService is healthy")
        except Exception as e:
            logger.error(f"Error fetching health status from MCPService: {e}")
# =============================
# INITIALIZATION
# =============================
# Load agent registration from YAML and initialize AgentHost client
agent_reg_model = load_agent_registration_yaml()
agent_host = AgentHost(agent_registration_model=agent_reg_model, agenthost_base_url=AGENTHOST_BASE_URL)
mcps_service = MCPService(mcps_base_url=MCPSERVICE_BASE_URL)


# =============================
# FASTAPI LIFESPAN EVENT
# =============================
# On startup, check AgentHost health, deregister, and register agent
@asynccontextmanager
async def lifespan(app):
    logger.info("Loading agenthost configuration...")
    agent_host.health_check()
    mcps_service.health_check()
    agent_host.deregister_agent()
    agent_host.register_agent()
    yield

# =============================
# FASTAPI APP AND ENDPOINTS
# =============================
app = FastAPI(lifespan=lifespan)

# Health check endpoint for this service
@app.get("/health")
def health():
    return {"status": "healthy"}

# =============================
# MAIN ENTRYPOINT
# =============================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
