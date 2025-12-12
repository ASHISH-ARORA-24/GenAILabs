# GenAILabs

A local LLM experimentation platform that provides a chat interface to interact with Ollama models through a unified proxy layer.

## 🎯 Overview

GenAILabs is a development environment for working with local language models. It combines Ollama's runtime with LiteLLM's proxy capabilities and a Streamlit chat interface to create a seamless experience for experimenting with small, efficient LLM models.

## 🏗️ Architecture

```
┌─────────────────┐
│   Streamlit UI  │  (Port 8501) - Web chat interface
│   (Frontend)    │
└────────┬────────┘
         │ OpenAI-compatible API
         ▼
┌─────────────────┐
│   Agent Host    │  (Port 8000) - Agent routing & orchestration
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LiteLLM Proxy  │  (Port 4100) - Model routing & authentication
│  + PostgreSQL   │  (Port 5433) - Usage tracking database
└────────┬────────┘
         │ Ollama API
         ▼
┌─────────────────┐
│     Ollama      │  (Port 11434) - LLM runtime
│  Models Runtime │  (tinyllama, qwen2.5, phi)
└─────────────────┘
```

### 📌 Port Allocation Scheme

- **4100**: LiteLLM Proxy (Model routing & API gateway)
- **5000-5999**: Reserved for Agent Services
- **6000-6999**: Reserved for MCP (Model Context Protocol) Services
- **8000**: AgentHost (Agent orchestration & routing)
- **8501**: Streamlit UI (Web interface)

## ✨ Features

- **Multiple Models**: Switch between tinyllama, qwen2.5, and phi models
- **Real-time Streaming**: See responses as they're generated
- **OpenAI-Compatible API**: Use standard OpenAI client libraries
- **Usage Tracking**: PostgreSQL-backed logging and analytics
- **Adjustable Parameters**: Control temperature, max tokens, and more
- **Clean Interface**: Modern Streamlit-based chat UI

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Ollama with models installed

### 1. Install Ollama Models

```bash
ollama pull tinyllama:1.1b
ollama pull qwen2.5:0.5b
ollama pull phi:latest
```

### 2. Start LiteLLM Hub

```bash
cd litellm_hub
cp .env.example .env  # Configure if needed
docker-compose up -d
```

### 3. Start AgentHost

```bash
cd agent_host
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
python main.py
```

AgentHost will be available at `http://localhost:8000`

### 4. Start MCP File Service

```bash
cd mcp_file_service
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
python main.py
```

MCP File Service will be available at `http://localhost:6001`
- API Documentation: `http://localhost:6001/docs`
- Endpoints: `/status`, `/list-files`, `/create-file`, `/delete-file`

### 5. Start Streamlit Interface

```bash
cd streamlit_service
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
streamlit run main.py
```

### 6. Open Your Browser

Navigate to `http://localhost:8501` and start chatting!

## 📁 Project Structure

```
GenAILabs/
├── architecture/          # Architecture documentation
│   ├── PHASE1_CURRENT.md  # Current implementation details
│   ├── PHASE2_PLANNED.md  # Future roadmap
│   └── README.md          # Detailed architecture overview
├── agent_host/           # Agent orchestration service
│   ├── main.py           # FastAPI agent routing
│   ├── pyproject.toml
│   └── README.md
├── litellm_hub/          # LiteLLM proxy service
│   ├── docker-compose.yml
│   ├── litellm_config.yaml
│   └── README.md
├── mcp_file_service/     # MCP file operations service
│   ├── main.py           # FastAPI file management
│   ├── pyproject.toml
│   └── README.md
├── streamlit_service/    # Streamlit chat interface
│   ├── main.py
│   ├── pyproject.toml
│   └── README.md
└── llm_models/           # Model information and docs
    └── README.md
```

## 🤖 Available Models

| Model | Size | Speed | Use Case |
|-------|------|-------|----------|
| **tinyllama** | 637 MB | ⚡⚡⚡ | Quick responses, simple tasks |
| **qwen2.5** | 397 MB | ⚡⚡⚡ | Fastest, ideal for testing |
| **phi** | 1.6 GB | ⚡⚡ | More capable, complex reasoning |

## 🔧 Configuration

### Environment Variables

**LiteLLM Hub** (`.env` in `litellm_hub/`):
```env
LITELLM_MASTER_KEY=sk-litellm-hub-local-123
LITELLM_PORT=4100
OLLAMA_BASE_URL=http://localhost:11434
POSTGRES_USER=litellm
POSTGRES_PASSWORD=litellm
```

**Streamlit Service** (`.env` in `streamlit_service/`):
```env
LITELLM_BASE_URL=http://localhost:4100/v1
LITELLM_API_KEY=sk-litellm-hub-local-123
```

## 🧪 Testing

### Test LiteLLM Connection

```bash
cd litellm_hub
./test_models.sh
```

### Test with Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4100/v1",
    api_key="sk-litellm-hub-local-123"
)

response = client.chat.completions.create(
    model="tinyllama",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## 🛠️ Management

### Check Services

```bash
# LiteLLM status
docker ps | grep litellm

# View logs
docker logs litellm_hub -f

# Ollama models
ollama list

# Health check
curl http://localhost:4100/health/liveliness
```

### Stop Services

```bash
# Stop LiteLLM
cd litellm_hub
docker-compose down

# Stop Streamlit
# Press Ctrl+C in the terminal running Streamlit
```

## 🗺️ Roadmap

### Phase 1 (Current)
✅ Basic chat interface  
✅ Multi-model support  
✅ LiteLLM proxy integration  
✅ Usage tracking database  

### Phase 2 (Planned)
- [ ] Agent orchestration layer
- [ ] RAG (Retrieval-Augmented Generation) pipeline
- [ ] MCP (Model Context Protocol) server support
- [ ] Advanced context management
- [ ] Multi-agent coordination

See [architecture/PHASE2_PLANNED.md](architecture/PHASE2_PLANNED.md) for details.

## 📚 Documentation

- [Architecture Overview](architecture/README.md) - Detailed system design
- [LiteLLM Hub Setup](litellm_hub/README.md) - Proxy configuration
- [Streamlit Interface](streamlit_service/README.md) - Frontend details
- [Model Information](llm_models/README.md) - Model specs

## 🐛 Troubleshooting

**Streamlit can't connect:**
- Verify LiteLLM is running: `docker ps`
- Check URL in `.env` matches setup

**Models not responding:**
- Ensure Ollama is running: `ollama list`
- Test Ollama directly: `curl http://localhost:11434/api/tags`

**Slow responses:**
- Try smaller models (qwen2.5 or tinyllama)
- Reduce max_tokens in Streamlit settings

## 📄 License

This is a development environment for experimenting with open-source LLM tools.

## 🙏 Credits

Built with:
- [Ollama](https://ollama.ai/) - LLM runtime
- [LiteLLM](https://github.com/BerriAI/litellm) - Model proxy
- [Streamlit](https://streamlit.io/) - Web interface
- [PostgreSQL](https://www.postgresql.org/) - Database

---

**Happy experimenting! 🚀**
