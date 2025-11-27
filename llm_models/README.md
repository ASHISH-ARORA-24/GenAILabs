
# llm_models

This directory is intended to contain various language model files, scripts, or related resources for the project.

## Ollama Installation (Ubuntu Linux)

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Starting Ollama Server

If Ollama is not running, start the server with:

```bash
ollama serve
```

## Running Models with Ollama

### Run phi:latest
```bash
ollama run phi:latest
```

### Run qwen2.5:0.5b
```bash
ollama run qwen2.5:0.5b
```

### Run tinyllama:1.1b
```bash
ollama run tinyllama:1.1b
```

## Testing the Models (cURL)

After starting a model, you can test it using the Ollama API (default: http://localhost:11434):

### Test phi:latest
```bash
curl http://localhost:11434/api/generate -d '{"model": "phi:latest", "prompt": "Hello, how are you?", "stream": false}'
```

### Test qwen2.5:0.5b
```bash
curl http://localhost:11434/api/generate -d '{"model": "qwen2.5:0.5b", "prompt": "Hello, how are you?", "stream": false}'
```

### Test tinyllama:1.1b
```bash
curl http://localhost:11434/api/generate -d '{"model": "tinyllama:1.1b", "prompt": "Hello, how are you?", "stream": false}'
```


## Removing an Ollama Model

To remove a model from Ollama, use:

```bash
ollama rm <model-name>
```

For example, to remove the phi:latest model:

```bash
ollama rm phi:latest
```
---

*Edit this README to provide more specific details as your project evolves.*
