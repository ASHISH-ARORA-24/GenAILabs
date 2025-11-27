# GenAILabs - Phase 2 (Planned Architecture)

## Overview

Future architecture introducing an Agent Host layer between Streamlit and LiteLLM to enable RAG, multi-agent orchestration, and MCP server integration.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Streamlit Chat Application                      │    │
│  │         (Port: 8501)                                    │    │
│  │                                                          │    │
│  │  • Enhanced UI with Agent Status                       │    │
│  │  • RAG Source Citations                                │    │
│  │  • Tool Execution Visualization                        │    │
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
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │           RAG Pipeline                          │   │    │
│  │  │                                                 │   │    │
│  │  │  • Vector Database (ChromaDB/FAISS)            │   │    │
│  │  │  • Embedding Models (sentence-transformers)    │   │    │
│  │  │  • Document Loaders (PDF, TXT, MD)             │   │    │
│  │  │  • Semantic Search & Retrieval                 │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │         Agent Manager                           │   │    │
│  │  │                                                 │   │    │
│  │  │  • Task Decomposition                          │   │    │
│  │  │  • Agent Selection & Routing                   │   │    │
│  │  │  • Multi-Agent Coordination                    │   │    │
│  │  │  • Result Aggregation                          │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │       MCP Server Integration                    │   │    │
│  │  │                                                 │   │    │
│  │  │  • Tool Registry & Discovery                   │   │    │
│  │  │  • MCP Protocol Handler                        │   │    │
│  │  │  • Tool Execution Engine                       │   │    │
│  │  │  • Custom Tool Development                     │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  • Context Management & History                        │    │
│  │  • Session Tracking                                    │    │
│  │  • Streaming Response Handler                          │    │
│  └────────────────────┬───────────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────────┘
                         │
                         │ LLM API Calls
                         │ (OpenAI Compatible)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Proxy Layer                                 │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            LiteLLM Proxy Server                         │    │
│  │            (Port: 4100)                                 │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│  ┌────────────────────┴───────────────────────────────────┐    │
│  │         PostgreSQL Database                             │    │
│  │         (Port: 5433)                                    │    │
│  └──────────────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────────────┘
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

## New Component: Agent Host Service

### Location & Technology
**Location:** `/agent_host` (to be created)
**Port:** 8000
**Technology:** FastAPI, LangChain/LlamaIndex, Python

### Core Modules

#### 1. RAG Pipeline
**Purpose:** Context-aware responses using document retrieval

**Components:**
- **Vector Database:** ChromaDB or FAISS for embedding storage
- **Embedding Model:** sentence-transformers for text vectorization
- **Document Loaders:** Support for PDF, TXT, MD, DOCX formats
- **Semantic Search:** Retrieve relevant context for queries

**Features:**
- Document ingestion and indexing
- Similarity search
- Context ranking and filtering
- Citation tracking

**Use Cases:**
- Answer questions from uploaded documents
- Provide context-aware responses
- Reference specific sections of documents

#### 2. Agent Manager
**Purpose:** Orchestrate multiple specialized agents

**Components:**
- **Task Analyzer:** Break complex queries into subtasks
- **Agent Router:** Select appropriate agent for each task
- **Coordinator:** Manage multi-agent workflows
- **Aggregator:** Combine results from multiple agents

**Agent Types (Examples):**
- Research Agent: Gather information
- Code Agent: Generate and explain code
- Analysis Agent: Analyze data and trends
- Summary Agent: Condense information

**Features:**
- Dynamic agent selection
- Parallel agent execution
- Result synthesis
- Error handling and fallback

#### 3. MCP Server Integration
**Purpose:** Extend capabilities with external tools

**Components:**
- **Tool Registry:** Catalog of available MCP servers
- **Protocol Handler:** Communicate with MCP servers
- **Execution Engine:** Run tools and capture results
- **Tool Builder:** Framework for custom tools

**MCP Servers (Examples):**
- File system operations
- Database queries
- API integrations
- Web scraping
- Calculator/math operations

**Features:**
- Dynamic tool discovery
- Tool parameter validation
- Result parsing and formatting
- Tool chaining

#### 4. Context Management
**Purpose:** Maintain conversation state and history

**Features:**
- Session tracking across requests
- Conversation history storage
- Context window optimization
- Token management
- Multi-turn dialogue support

### API Endpoints (Planned)

```python
# Chat endpoint (enhanced with RAG and agents)
POST /v1/chat/completions
{
    "messages": [...],
    "model": "phi",
    "use_rag": true,
    "use_agents": true,
    "enable_tools": true
}

# RAG document management
POST /v1/rag/documents
GET /v1/rag/documents
DELETE /v1/rag/documents/{id}

# Agent management
GET /v1/agents
POST /v1/agents/execute

# MCP server management
GET /v1/tools
POST /v1/tools/execute
GET /v1/tools/{tool_id}/schema
```

## Enhanced Data Flow

### RAG-Enhanced Query Flow

1. **User Query** → Streamlit sends request to Agent Host
2. **Context Retrieval** → Agent Host queries vector DB for relevant docs
3. **Prompt Enhancement** → Inject retrieved context into prompt
4. **LLM Call** → Agent Host → LiteLLM → Ollama
5. **Response** → Return with citations
6. **Display** → Streamlit shows response + sources

### Multi-Agent Workflow

1. **Complex Query** → "Analyze this code and suggest improvements"
2. **Task Decomposition** → Agent Manager breaks into:
   - Understand code (Analysis Agent)
   - Identify issues (Code Review Agent)
   - Suggest fixes (Code Generation Agent)
3. **Parallel Execution** → Agents work simultaneously
4. **Result Aggregation** → Combine insights
5. **Response** → Comprehensive analysis with suggestions

### Tool-Augmented Response

1. **Query with Tool Need** → "What files are in /home/user?"
2. **Tool Selection** → Identify filesystem MCP server
3. **Tool Execution** → Run ls command via MCP
4. **Context Enhancement** → Add results to LLM prompt
5. **Natural Response** → LLM formats tool output naturally

## Technology Stack

### Core Framework
- **API Framework:** FastAPI
- **Async Runtime:** asyncio, aiohttp
- **Validation:** Pydantic v2

### RAG Components
- **Vector DB:** ChromaDB (default) or FAISS
- **Embeddings:** sentence-transformers (all-MiniLM-L6-v2)
- **Document Processing:** LangChain document loaders
- **Chunking:** LangChain text splitters

### Agent Framework
- **Orchestration:** LangChain or LlamaIndex
- **Agent Types:** ReAct, Plan-and-Execute
- **Memory:** ConversationBufferMemory, VectorStoreMemory

### MCP Integration
- **Protocol:** Model Context Protocol SDK
- **Transport:** HTTP/SSE or stdio
- **Tool Schema:** JSON Schema validation

### Database
- **Session Storage:** SQLite or PostgreSQL
- **Vector Storage:** ChromaDB or FAISS
- **Cache:** Redis (optional)

## Configuration

### Agent Host `.env`
```env
# Service
AGENT_HOST_PORT=8000
AGENT_HOST_HOST=0.0.0.0

# LiteLLM Connection
LITELLM_BASE_URL=http://localhost:4100/v1
LITELLM_API_KEY=sk-litellm-hub-local-123

# RAG Configuration
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/vectordb
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Agent Configuration
AGENT_FRAMEWORK=langchain
MAX_AGENT_ITERATIONS=5
ENABLE_AGENT_MEMORY=true

# MCP Configuration
MCP_SERVERS_PATH=./mcp_servers
ENABLE_MCP=true
```

## Implementation Phases

### Phase 2.1: Basic Agent Host
- [ ] Create FastAPI service
- [ ] Implement proxy to LiteLLM
- [ ] Add basic session management
- [ ] Update Streamlit to use Agent Host

### Phase 2.2: RAG Implementation
- [ ] Set up ChromaDB
- [ ] Implement document ingestion
- [ ] Add semantic search
- [ ] Create RAG endpoints
- [ ] Update UI for document upload

### Phase 2.3: Agent Framework
- [ ] Integrate LangChain
- [ ] Create agent templates
- [ ] Implement agent manager
- [ ] Add multi-agent coordination
- [ ] Update UI to show agent activity

### Phase 2.4: MCP Integration
- [ ] Implement MCP protocol
- [ ] Create tool registry
- [ ] Build execution engine
- [ ] Develop sample MCP servers
- [ ] Add tool UI in Streamlit

## Benefits of Phase 2

### For Users
- ✅ Answer questions from documents (RAG)
- ✅ Complex task handling (agents)
- ✅ Extended capabilities (MCP tools)
- ✅ Better context awareness
- ✅ More accurate responses

### For Development
- ✅ Modular architecture
- ✅ Easy to add new capabilities
- ✅ Separate concerns (UI vs logic)
- ✅ Testable components
- ✅ Scalable design

### For Future
- ✅ Ready for multi-user support
- ✅ Pluggable tool ecosystem
- ✅ Agent marketplace potential
- ✅ API for external integrations
- ✅ Cloud deployment ready

## Migration from Phase 1

### What Changes
- Streamlit now calls Agent Host (port 8000) instead of LiteLLM (port 4100)
- Agent Host handles all business logic
- LiteLLM becomes internal service (called by Agent Host)

### What Stays the Same
- Streamlit UI (minimal changes)
- LiteLLM configuration
- Ollama models
- PostgreSQL database

### Backward Compatibility
- Phase 1 mode: Set `USE_AGENT_HOST=false` in Streamlit `.env`
- Direct LiteLLM access still available for simple queries

## Performance Considerations

### RAG
- Embedding generation: ~50-100ms
- Vector search: ~10-50ms
- Impact: +100-150ms per query

### Agents
- Single agent: +200-500ms overhead
- Multi-agent: Parallel execution, ~500-1000ms
- Depends on task complexity

### MCP Tools
- Tool execution: Varies by tool
- Network calls: +50-200ms
- File operations: ~10-50ms

### Optimization Strategies
- Cache embeddings
- Parallel agent execution
- Async tool calls
- Result caching
- Pre-load models

## Security Enhancements

### Phase 2 Security
- Agent Host authentication
- Tool permission system
- RAG document access control
- Rate limiting per user
- Input validation and sanitization

## Monitoring & Observability

### Metrics to Track
- Agent execution time
- RAG retrieval quality
- Tool success/failure rates
- Token usage per component
- Cache hit rates

### Logging
- Agent decisions and reasoning
- Tool executions
- RAG queries and results
- Error traces
- Performance metrics

## Next Steps

1. Review and approve Phase 2 design
2. Set up Agent Host project structure
3. Implement Phase 2.1 (basic service)
4. Test integration with existing services
5. Incrementally add RAG, agents, MCP

**→ See `PHASE1_CURRENT.md` for current working system**
