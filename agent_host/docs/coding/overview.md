# AgentHost Implementation Overview

This document outlines the step-by-step implementation plan for building the AgentHost system.

---

## Segment 1 — Create AgentHost Skeleton

Create a minimal Python structure (FastAPI or plain Python module).

**One endpoint/function:**
- "AgentHost received your query" (hardcoded).

Confirm Streamlit can talk to AgentHost.

### 🎯 Goal
Just connectivity.
- No registry.
- No LLM.
- No agents.

---

## Segment 2 — Add In-Memory Agent Registry

Create a simple registry structure (dict or class).

**Add methods:**
- `register_agent()`
- `list_agents()`

Hardcode ONE dummy agent in the registry (no real agent yet).

### 🎯 Goal
AgentHost knows what agents exist.

---

## Segment 3 — Add a Minimal DummyAgent

Create a simple agent:

**Receives a query and returns:**
```
"DummyAgent got: <query>"
```

Register it using Segment 1 rules.

### 🎯 Goal
End-to-end flow: Host → Agent → Host.

---

## Segment 4 — Add Routing Mode (auto or manual)

Accept `routing_mode` in the request.

**If manual:**
- Directly call the agent (no LLM router yet).

**If auto:**
- For now just pick DummyAgent automatically (LLM router comes later).

### 🎯 Goal
Learn manual vs auto flow before involving LLM.

---

## Segment 5 — First Minimal LLM Router

Build the router LLM call:

- Send user query + agent names + description (simple version).
- LLM returns just agent name.
- Don't include curated prompts or examples yet.

### 🎯 Goal
LLM decides which agent (even with only 1 agent).

---

## Segment 6 — Full LLM Router with Curated Prompts

Expand router prompt:

- `curated_routing_prompts`
- `example_queries`
- `capability_tags`

Parse LLM structured output.

### 🎯 Goal
Complete, intelligent agent selection.

---

## Segment 7 — Agent Execution Contract

Implement the actual `ExecutionRequest` → `ExecutionResponse` flow.

**Agents handle:**
- `request_id`
- `status`
- `result`

### 🎯 Goal
Proper, structured communication with agents.

---

## Segment 8 — Add Final LLM Composer

Build the composer:

- Takes execution result
- Formats final output for UI

**Support:**
- `success`
- `partial`
- `error`

### 🎯 Goal
You get user-friendly responses from raw agent outputs.

---

## Segment 9 — Add Basic Fallback Logic

When no agent selected:

- Fallback to simple LLM chat
- Or return "not capable"

### 🎯 Goal
System never breaks.

---

## Segment 10 — Add Logging and Tracing

**Basic logs:**
- routing decisions
- agent calls
- errors
- timings

Store logs in file or console.

### 🎯 Goal
Observability and debugging support.
