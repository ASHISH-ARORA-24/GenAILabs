#!/bin/bash

# Test script for LiteLLM models
LITELLM_URL="http://localhost:4100"
API_KEY="sk-litellm-hub-local-123"

echo "Testing LiteLLM Models..."
echo "=========================="
echo

# Test 1: TinyLlama
echo "1. Testing TinyLlama model:"
curl -s -X POST $LITELLM_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "tinyllama",
    "messages": [{"role": "user", "content": "Say hi in 5 words"}],
    "max_tokens": 20
  }' | python3 -m json.tool
echo
echo "---"
echo

# Test 2: Qwen2.5
echo "2. Testing Qwen2.5 model:"
curl -s -X POST $LITELLM_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "qwen2.5",
    "messages": [{"role": "user", "content": "What is AI in one sentence?"}],
    "max_tokens": 30
  }' | python3 -m json.tool
echo
echo "---"
echo

# Test 3: Phi
echo "3. Testing Phi model:"
curl -s -X POST $LITELLM_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "phi",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 30
  }' | python3 -m json.tool
echo
echo "---"
echo

echo "4. Available models:"
curl -s -X GET $LITELLM_URL/v1/models \
  -H "Authorization: Bearer $API_KEY" | python3 -m json.tool

echo
echo "=========================="
echo "All tests completed!"
