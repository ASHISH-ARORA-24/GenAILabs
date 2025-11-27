# GenAILabs - Phase 1 (Current Architecture)

## Overview

Current implementation of GenAILabs platform with direct integration between Streamlit UI and LiteLLM proxy for local LLM access.

## Architecture Diagram

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

## Configuration

### Streamlit Service `.env`
```env
LITELLM_BASE_URL=http://localhost:4100/v1
LITELLM_API_KEY=sk-litellm-hub-local-123
```

### LiteLLM Hub `.env`
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

- **Frontend:** Streamlit 1.51.0
- **Proxy:** LiteLLM (Docker)
- **Database:** PostgreSQL 16
- **LLM Runtime:** Ollama
- **Models:** TinyLlama 1.1B, Qwen 2.5 0.5B, Phi 3B
- **Containerization:** Docker & Docker Compose
- **Package Management:** uv
- **Python:** 3.12+

## Cost

**Total Monthly Cost: $10**
- GitHub Copilot: $10/month (includes unlimited chat)
- All other services: $0 (open source, running locally)

## What's Working

✅ Direct chat with local LLM models
✅ Model switching in UI
✅ Real-time streaming responses
✅ Request logging and tracking
✅ OpenAI-compatible API
✅ Multiple model support

## Limitations

⚠️ No context retrieval (RAG)
⚠️ No agent capabilities
⚠️ No tool/function calling
⚠️ No MCP server integration
⚠️ Limited to simple chat interactions

**→ See `PHASE2_PLANNED.md` for upcoming enhancements**
