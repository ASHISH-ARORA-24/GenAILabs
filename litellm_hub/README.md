# LiteLLM Hub with Ollama Models

This setup provides a LiteLLM proxy server with PostgreSQL database, configured to work with your local Ollama models.

## Components

- **PostgreSQL**: Database on port `5433` (configurable via `.env`)
- **LiteLLM**: Proxy server on port `4100` (configurable via `.env`)
- **Master Key**: Configured in `.env` file

## Available Models

1. **phi** (phi:latest) - 1.6 GB
2. **qwen2.5** (qwen2.5:0.5b) - 397 MB
3. **tinyllama** (tinyllama:1.1b) - 637 MB

## Quick Start

### 1. Configure Environment
Copy the example environment file and update with your values:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

### 2. Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker logs litellm_hub -f
```

## Testing

### Using the Test Script
```bash
./test_models.sh
```

### Manual Testing

#### Test with curl
```bash
curl -X POST http://localhost:4100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-litellm-hub-local-123" \
  -d '{
    "model": "tinyllama",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

#### Test with Python
```python
import requests

url = "http://localhost:4100/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-litellm-hub-local-123"
}
data = {
    "model": "qwen2.5",
    "messages": [{"role": "user", "content": "What is AI?"}],
    "max_tokens": 50
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### List Available Models
```bash
curl -X GET http://localhost:4100/v1/models \
  -H "Authorization: Bearer sk-litellm-hub-local-123"
```

## OpenAI Compatible API

The LiteLLM proxy is fully compatible with OpenAI's API, so you can use it with any OpenAI client library:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4100/v1",
    api_key="sk-litellm-hub-local-123"
)

response = client.chat.completions.create(
    model="phi",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Configuration Files

- `.env` - Environment variables (passwords, URLs, keys) - **DO NOT COMMIT**
- `.env.example` - Template for environment variables
- `docker-compose.yml` - Docker services configuration
- `litellm_config.yaml` - LiteLLM model configuration
- `.gitignore` - Protects sensitive files from git

## Requirements

- Docker and Docker Compose
- Ollama running locally on port 11434
- Available Ollama models (phi, qwen2.5, tinyllama)

## Troubleshooting

If models aren't responding:
1. Check if Ollama is running: `ollama list`
2. Check container logs: `docker logs litellm_hub`
3. Verify containers are up: `docker ps | grep litellm`
4. Test Ollama directly: `curl http://localhost:11434/api/tags`
