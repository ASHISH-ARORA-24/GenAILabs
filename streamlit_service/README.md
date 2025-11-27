# LiteLLM Streamlit Chat Interface

A modern chat interface built with Streamlit that connects to your LiteLLM Hub to interact with local Ollama models.

## Features

- 🤖 **Multiple Models**: Switch between phi, qwen2.5, and tinyllama
- 💬 **Real-time Streaming**: See responses as they're generated
- ⚙️ **Adjustable Settings**: Control temperature and max tokens
- 📊 **Chat Metrics**: Track messages, model, and settings
- 🎨 **Clean UI**: Modern, responsive interface

## Setup

### 1. Install Dependencies
```bash
uv venv .venv
source .venv/bin/activate
uv add streamlit openai python-dotenv
```

### 2. Configure Environment
Create a `.env` file:
```env
LITELLM_BASE_URL=http://localhost:4100/v1
LITELLM_API_KEY=sk-litellm-hub-local-123
```

### 3. Run the Application
```bash
streamlit run main.py
```

The app will open at `http://localhost:8501`

## Usage

1. **Select a Model**: Use the sidebar dropdown to choose your preferred LLM
2. **Adjust Settings**: 
   - Temperature: Controls randomness (0.0 = deterministic, 2.0 = very random)
   - Max Tokens: Limits response length
3. **Start Chatting**: Type your message in the chat input
4. **Clear History**: Use the "Clear Chat" button to start fresh

## Available Models

- **tinyllama** (637 MB) - Fast and lightweight
- **qwen2.5** (397 MB) - Smallest and fastest
- **phi** (1.6 GB) - More capable, slower

## Requirements

- Python 3.12+
- LiteLLM Hub running on port 4100
- Ollama models installed locally

## Troubleshooting

**Connection Error:**
- Ensure LiteLLM Hub is running: `docker ps | grep litellm`
- Check the URL in `.env` matches your setup

**Models Not Loading:**
- Verify models are available: `curl http://localhost:4100/v1/models -H "Authorization: Bearer sk-litellm-hub-local-123"`

**Slow Responses:**
- Try a smaller model (tinyllama or qwen2.5)
- Reduce max_tokens setting
