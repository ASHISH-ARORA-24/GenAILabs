# GenAILabs System Architecture

## Overview

This document describes the architecture of the GenAILabs platform, which provides a chat interface to interact with local LLM models through a unified proxy.

## Architecture Diagram

### Current Architecture (Phase 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Streamlit Chat Application                      │    │
│  │         (Port: 8501)                                    │    │
│  │                                                          │    │
│  │  • Model Selection (phi, qwen2.5, tinyllama)           │    │
│  │  • Real-time Streaming Chat                            │    │
│  │  • Temperature & Token Controls                        │    │
│  │  • Chat History Management                             │    │
│  └────────────────────┬───────────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         │ HTTP REST API
                         │ (OpenAI Compatible)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Proxy Layer                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            LiteLLM Proxy Server                         │    │
│  │            (Port: 4100)                                 │    │
│  │                                                          │    │
│  │  • API Key Authentication                              │    │
│  │  • Model Routing & Load Balancing                      │    │
│  │  • Request/Response Logging                            │    │
│  │  • OpenAI API Compatibility                            │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│  ┌────────────────────┴───────────────────────────────────┐    │
│  │         PostgreSQL Database                             │    │
│  │         (Port: 5433)                                    │    │
│  │                                                          │    │
│  │  • Usage Tracking                                       │    │
│  │  • API Key Management                                   │    │
│  │  • Request Logs                                         │    │
│  └──────────────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         │ Ollama API
                         │ (localhost:11434)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Models Layer                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Ollama Runtime                             │    │
│  │              (Port: 11434)                              │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │    │
│  │  │ TinyLlama    │  │  Qwen 2.5    │  │     Phi      │ │    │
│  │  │  (1.1B)      │  │   (0.5B)     │  │    (3B)      │ │    │
│  │  │  637 MB      │  │   397 MB     │  │   1.6 GB     │ │    │
│  │  │  ⚡⚡⚡       │  │   ⚡⚡⚡      │  │    ⚡⚡       │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Future Architecture (Phase 2 - Planned)

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Streamlit Chat Application                      │    │
│  │         (Port: 8501)                                    │    │
│  └────────────────────┬───────────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         │ HTTP REST API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Orchestration Layer                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Agent Host Service                         │    │
│  │              (Port: 8000)                               │    │
│  │                                                          │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │    │
│  │  │    RAG     │  │   Agents   │  │  MCP Servers   │   │    │
│  │  │  Pipeline  │  │  Manager   │  │   (Tools)      │   │    │
│  │  └────────────┘  └────────────┘  └────────────────┘   │    │
│  │                                                          │    │
│  │  • Context Management                                   │    │
│  │  • Tool Orchestration                                   │    │
│  │  • Agent Coordination                                   │    │
│  │  • RAG Integration                                      │    │
│  └────────────────────┬───────────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         │ LLM API Calls
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Proxy Layer                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            LiteLLM Proxy Server                         │    │
│  │            (Port: 4100)                                 │    │
│  └────────────────────┬───────────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         │ Ollama API
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Models Layer                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Ollama Runtime                             │    │
│  │              (Port: 11434)                              │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │    │
│  │  │ TinyLlama    │  │  Qwen 2.5    │  │     Phi      │ │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Streamlit Chat Application
**Location:** `/streamlit_service`
**Port:** 8501
**Technology:** Python, Streamlit, OpenAI SDK

**Features:**
- Web-based chat interface
- Model selection dropdown
- Real-time response streaming
- Adjustable parameters (temperature, max tokens)
- Chat history management
- Connection status monitoring

**Key Files:**
- `main.py` - Main application
- `.env` - Configuration (API keys, URLs)
- `pyproject.toml` - Dependencies

### 2. LiteLLM Proxy Server
**Location:** `/litellm_hub`
**Port:** 4100
**Technology:** Docker, LiteLLM, PostgreSQL

**Features:**
- OpenAI-compatible API interface
- Multi-model routing
- Request authentication & authorization
- Usage tracking and analytics
- Load balancing
- Database-backed persistence

**Key Files:**
- `docker-compose.yml` - Service orchestration
- `litellm_config.yaml` - Model configurations
- `.env` - Environment variables

**Services:**
- LiteLLM Proxy (port 4100)
- PostgreSQL Database (port 5433)

### 3. Ollama Runtime
**Location:** System-level service
**Port:** 11434
**Technology:** Ollama

**Available Models:**
- **tinyllama:1.1b** - Lightweight, fast responses
- **qwen2.5:0.5b** - Smallest model, fastest
- **phi:latest** - More capable, larger model

### 4. Agent Host Service (Phase 2 - Planned)
**Location:** `/agent_host` (planned)
**Port:** 8000 (planned)
**Technology:** FastAPI, LangChain/LlamaIndex, Python

**Planned Features:**
- **RAG Pipeline**: Retrieval-Augmented Generation for context-aware responses
  - Vector database integration (ChromaDB, FAISS)
  - Document ingestion and indexing
  - Semantic search capabilities
  
- **Agent Manager**: Multi-agent orchestration
  - Task decomposition
  - Agent routing and delegation
  - Result aggregation
  
- **MCP Integration**: Model Context Protocol servers
  - Tool discovery and registration
  - Tool execution and monitoring
  - Custom tool development
  
- **Context Management**:
  - Conversation history
  - Session management
  - Context window optimization

**Key Components:**
- API Gateway for Streamlit
- RAG service (vector DB + embeddings)
- Agent orchestrator
- MCP server registry
- LiteLLM client

## Data Flow

### Chat Request Flow

1. **User Input** → User types message in Streamlit UI
2. **API Request** → Streamlit sends POST request to LiteLLM
   ```
   POST http://localhost:4100/v1/chat/completions
   Headers: Authorization: Bearer sk-litellm-hub-local-123
   Body: { model, messages, temperature, max_tokens }
   ```
3. **Authentication** → LiteLLM validates API key
4. **Model Routing** → LiteLLM routes to appropriate Ollama model
5. **LLM Processing** → Ollama generates response
6. **Response Streaming** → Response streamed back through chain
7. **UI Update** → Streamlit displays streaming response

### Model List Flow

1. **Request** → Streamlit requests available models
2. **Query** → LiteLLM queries configured models
3. **Response** → Returns list of model IDs
4. **UI Update** → Dropdown populated with models

## Network Configuration

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| Streamlit | 8501 | HTTP | localhost |
| LiteLLM | 4100 | HTTP | localhost |
| PostgreSQL | 5433 | TCP | localhost |
| Ollama | 11434 | HTTP | localhost |

## Security

- **API Authentication:** Bearer token required for LiteLLM access
- **Network Isolation:** All services on localhost
- **Environment Variables:** Sensitive data in `.env` files
- **Git Protection:** `.gitignore` prevents credential commits

## Configuration Files

### Streamlit Service
```env
LITELLM_BASE_URL=http://localhost:4100/v1
LITELLM_API_KEY=sk-litellm-hub-local-123
```

### LiteLLM Hub
```env
POSTGRES_USER=litellm
POSTGRES_PASSWORD=litellm
POSTGRES_DB=litellm
POSTGRES_PORT=5433
LITELLM_MASTER_KEY=sk-litellm-hub-local-123
LITELLM_PORT=4100
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://litellm:litellm@localhost:5433/litellm
```

## Deployment

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- uv package manager
- Ollama with downloaded models

### Start Services

1. **Start LiteLLM Hub:**
   ```bash
   cd litellm_hub
   docker-compose up -d
   ```

2. **Start Streamlit:**
   ```bash
   cd streamlit_service
   source .venv/bin/activate
   streamlit run main.py
   ```

3. **Access Application:**
   - Chat UI: http://localhost:8501
   - LiteLLM API: http://localhost:4100

## Phase 2 Roadmap

### Agent Host Implementation

**Core Features:**
1. **FastAPI Service**
   - RESTful API endpoints
   - WebSocket support for streaming
   - Async processing
   - API documentation (OpenAPI/Swagger)

2. **RAG Integration**
   - Vector database (ChromaDB/FAISS/Qdrant)
   - Embedding models (sentence-transformers)
   - Document loaders (PDF, TXT, MD, etc.)
   - Semantic search and retrieval

3. **Agent Framework**
   - LangChain/LlamaIndex integration
   - Custom agent definitions
   - Tool/function calling
   - Agent memory and state

4. **MCP Server Support**
   - MCP protocol implementation
   - Tool registration and discovery
   - Tool execution framework
   - Custom MCP server development

5. **Context Management**
   - Session tracking
   - Conversation history
   - Context compression
   - Token optimization

**Benefits:**
- Decoupled architecture (separation of concerns)
- Easier to add new capabilities without touching Streamlit
- Centralized logic for agents, RAG, and tools
- Can support multiple frontends (Streamlit, API clients, etc.)
- Better testing and maintenance

**Technology Stack:**
- **Framework:** FastAPI
- **RAG:** LangChain or LlamaIndex
- **Vector DB:** ChromaDB or FAISS
- **Embeddings:** sentence-transformers
- **Agents:** LangChain Agents or AutoGPT
- **MCP:** Model Context Protocol SDK

### Phase 2 Data Flow

1. User → Streamlit UI
2. Streamlit → Agent Host API
3. Agent Host processes request:
   - Checks if RAG needed (query vector DB)
   - Determines which agent/tool to use
   - Calls MCP servers if needed
   - Constructs enhanced prompt
4. Agent Host → LiteLLM (with enriched context)
5. LiteLLM → Ollama models
6. Response streams back through chain
7. Agent Host post-processes (if needed)
8. Streamlit displays result

## Scaling Considerations

### Current Setup (Phase 1)
- Single instance of each service
- Localhost only
- Suitable for development and personal use

### Future Enhancements (Phase 2+)
- Load balancing for multiple LiteLLM instances
- Remote model hosting
- Authentication service
- API rate limiting
- Response caching
- Multi-user support
- Cloud deployment
- Distributed agent execution
- Vector DB clustering

## Monitoring

### Health Checks
```bash
# Check Ollama
ollama list

# Check LiteLLM
curl http://localhost:4100/health/liveliness

# Check PostgreSQL
docker logs litellm_hub_postgres

# Check Streamlit
curl http://localhost:8501
```

### Logs
```bash
# LiteLLM logs
docker logs litellm_hub -f

# PostgreSQL logs
docker logs litellm_hub_postgres -f
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Streamlit can't connect to LiteLLM | Verify LiteLLM is running on port 4100 |
| LiteLLM can't reach Ollama | Check Ollama is listening on port 11434 |
| Models not loading | Verify models are installed with `ollama list` |
| Database connection error | Check PostgreSQL container is healthy |
| Authentication error | Verify API key matches in both `.env` files |

## Technology Stack

- **Frontend:** Streamlit
- **Proxy:** LiteLLM
- **Database:** PostgreSQL 16
- **LLM Runtime:** Ollama
- **Models:** TinyLlama, Qwen 2.5, Phi
- **Containerization:** Docker & Docker Compose
- **Package Management:** uv
- **Python:** 3.12+

## License & Credits

This is a development environment for experimenting with local LLM models using open-source tools.

**Key Technologies:**
- [Streamlit](https://streamlit.io/)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [Ollama](https://ollama.ai/)
- [PostgreSQL](https://www.postgresql.org/)
