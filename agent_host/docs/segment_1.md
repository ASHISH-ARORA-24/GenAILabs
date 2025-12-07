# Segment 1 – Agent Registry Structure (Design Only)

## 1. Purpose of the Agent Registry

The registry is the **single source of truth** that AgentHost uses to:

- Know which agents exist
- Understand what each agent can do
- Decide routing using LLM
- Know how to call each agent
- Format final responses correctly

> The registry is the "directory" of the multi-agent system.

---

## 2. What an Agent MUST Provide When Registering

### ✅ 2.1 `agent_name` (string)

**What:** Unique identifier.  
**Why:** Router LLM needs easy names; logs & debugging need consistent IDs.

**Examples:**
- `"DevOpsAgent"`
- `"RAGAgent"`
- `"CostAnalysisAgent"`

---

### ✅ 2.2 `description` (short paragraph)

**What:** One or two lines describing the agent's purpose.  
**Why:** Used by LLM router to understand agent specialization.

**Example:**
```
"Handles all cloud infrastructure operations related to Azure, GitHub runners, scaling, cost insights, and CI/CD troubleshooting."
```

---

### ✅ 2.3 `capability_tags` (list of keywords)

**What:** Tags like `["azure", "github", "costs", "infrastructure", "runners"]`.  
**Why:** Helps AgentHost pre-filter agents and helps router LLM understand domain quickly.

---

### ✅ 2.4 `curated_routing_prompts` (text block)

**This is very important.**

**What:** A curated description telling the router LLM when this agent should be selected.  
**Why:** Makes routing accurate and stable.

**Example curated prompt:**
```
"Select this agent whenever the query relates to Azure VM management, GitHub runner scaling, cost optimization, pipeline performance, infrastructure diagnostics, or cloud resources."
```

---

### ✅ 2.5 `example_queries` (3–5 examples)

**What:** Few-shot examples to guide the router LLM.  
**Why:** Examples dramatically increase routing accuracy.

**Examples:**
- `"Check Azure VM costs for RunnerScale for last 7 days."`
- `"Scale GitHub runners based on pending workflow queue."`
- `"Explain why a GitHub runner went offline."`

---

## Optional but Recommended

### 🔹 2.6 `usage_hints` (response-format guidance for the LLM composer)

**What:** Instructions to help LLM format the final response.  
**Why:** Each agent produces different types of data (technical logs, JSON, tables…).

**Example usage hint:**
```
"When formatting results from this agent, always include a summary of cloud cost impact and the recommended next action."
```

---

### 🔹 2.7 `api_endpoint` / `handler`

**What:** How AgentHost should call this agent.  
**Why:** Required for actual execution.

**This could be:**
- HTTP endpoint
- Local Python module
- gRPC endpoint
- MCP server address

For design phase, just treat it as: `"how_to_call_me": "<address or handler>"`.

---

### 🔹 2.8 `health_status` (dynamic)

**Not part of registration**, but maintained by AgentHost.

**Values:** `"healthy"`, `"unhealthy"`, `"unknown"`.

---

### 🔹 2.9 `version` (string)

For future debugging and agent upgrades.

**Example:** `"v0.1.0"`

---

## 3. Final Registry Structure (Human-readable spec)

Here is the conceptual structure:

```yaml
agent_registry_entry:
  agent_name: string
  description: string
  capability_tags: [string]
  curated_routing_prompts: string
  example_queries: [string]
  usage_hints: string (optional)
  how_to_call: string or object
  version: string (optional)
  health_status: string (dynamic, maintained by AgentHost)
```
