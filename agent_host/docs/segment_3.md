# Segment 3 – Routing Design (LLM Router + Manual Override)

## 1. Goal of the Routing Layer

The routing layer decides who should handle a user query:

**Either:**
- An independent agent (DevOpsAgent, RAGAgent, etc.), or
- No agent (fallback to plain LLM answer / "not capable").

**Routing can happen in two ways:**
1. **Auto routing** – LLM decides the best agent.
2. **Manual routing** – User directly chooses a specific agent.

AgentHost handles both.

---

## 2. Routing Modes

Every request coming from Streamlit to AgentHost includes a routing mode:

```yaml
routing_mode: "auto" | "manual"
selected_agent: string (optional, only used for "manual")
```

### 2.1 `auto` mode (default)

User just types a query in the UI.

**Streamlit sends:**
- `routing_mode = "auto"`
- `selected_agent = null`

**AgentHost:**
- Uses LLM Router to choose the best agent (or none).

### 2.2 `manual` mode

UI may provide a dropdown: "Choose specific agent (optional)".

If user selects an agent (e.g., DevOpsAgent), **Streamlit sends:**
- `routing_mode = "manual"`
- `selected_agent = "DevOpsAgent"`

**AgentHost:**
- Skips LLM routing.
- Directly calls DevOpsAgent (if it exists in registry).
- If `selected_agent` is not found → return a clear error or fallback (design choice).

---

## 3. Router Input (for auto mode)

When `routing_mode = "auto"`, AgentHost needs to build an input for the LLM Router.

### 3.1 Inputs sent to the router LLM

```yaml
RouterInput:
  user_query: string
  agents: [
    {
      agent_name: string
      description: string
      capability_tags: [string]
      curated_routing_prompts: string
      example_queries: [string]  # top 2–3 examples per agent
    },
    ...
  ]
```

### Notes:

AgentHost condenses the registry:
- It doesn't have to send every field.
- It can limit `example_queries` to a few best ones.
- Later, you can pre-filter agents (e.g., by tags) before sending to the LLM if needed.

---

## 4. Router Prompt Structure (LLM call)

The LLM Router prompt has 3 parts:

### 4.1 System Message – define LLM's role

**Conceptual content:**
- "You are a router."
- "Your job is to choose the single best agent or none if no agent fits."
- "Use agent descriptions, tags, curated guidance, and example queries."
- "Always respond in a strict structured format (we define it below)."

### 4.2 Context Message – list of agents

This contains the agent list, formatted in a readable way:

**Example structure:**

```
You have the following agents:

1) Agent Name: DevOpsAgent
   Description: Handles Azure, GitHub runners, CI/CD infrastructure, and cloud cost insights.
   Tags: ["azure", "github", "runners", "costs"]
   When to use: Select this agent for queries related to cloud infrastructure, Azure VMs, GitHub Actions runners, cost optimisation, pipeline diagnostics, and RunnerScale platform operations.
   Example queries:
     - "Check Azure VM costs for RunnerScale for last 7 days."
     - "Scale GitHub runners based on pending workflow queue."

2) Agent Name: RAGAgent
   Description: Answers questions using internal documents and knowledge base.
   Tags: ["documents", "knowledge_base", "policy", "architecture_docs"]
   When to use: Select this agent for queries that require reading internal documents, policies, architecture designs, or knowledge base content.
   Example queries:
     - "Summarize our GenAILab architecture document."
     - "What does our internal policy say about data retention?"
```

This is where your **curated routing prompts** + **example queries** directly help the LLM.

### 4.3 User Message – actual query

**Example:**

```
User query:
"Check Azure VM costs for RunnerScale for last 7 days and tell me if we overspent."
```

---

## 5. Router Output Schema (from LLM)

AgentHost needs the LLM to respond in a machine-friendly shape so it can parse it easily.

We define this logical output:

```yaml
RouterOutput:
  selected_agent: string   # agent_name or "none"
  confidence: number       # 0.0–1.0 (optional but useful)
  reasoning: string        # brief explanation used for logs/debugging
```

### Examples:

#### 5.1 Agent selected

```yaml
selected_agent: "DevOpsAgent"
confidence: 0.92
reasoning: "The query is about Azure VM costs and RunnerScale infrastructure, which matches DevOpsAgent's description and examples."
```

#### 5.2 No agent selected

```yaml
selected_agent: "none"
confidence: 0.40
reasoning: "The query does not clearly match any registered agent's domain."
```

### Future Extension

Initially, we use **single-agent routing** only.

Later, you can extend this to:

```yaml
selected_agents: [
  { agent_name: "DevOpsAgent", confidence: 0.9 },
  { agent_name: "RAGAgent", confidence: 0.6 }
]
```

for **multi-agent flows**.

---

## 6. AgentHost Routing Logic (full picture)

Putting everything together:

### 6.1 When a request arrives from Streamlit

**Incoming conceptual request:**

```yaml
AgentHostRequest:
  user_query: string
  routing_mode: "auto" | "manual"
  selected_agent: string (optional)
```

### 6.2 Decision flow inside AgentHost

#### If `routing_mode == "manual"`:

1. Check if `selected_agent` exists in Agent Registry.
2. **If YES** → directly call that agent (skip LLM router).
3. **If NO** → return a clear error (e.g., "Agent not found in registry.").

#### If `routing_mode == "auto"` (or missing):

1. **Build `RouterInput`:**
   - `user_query`
   - `agents` (condensed registry entries)

2. **Call LLM Router** using the prompt structure from Sections 4.1–4.3.

3. **Parse `RouterOutput`:**
   - **If `selected_agent == "none"`:**
     - Do not call any agent → move to fallback behaviour.
   - **If `selected_agent` is not found in registry:**
     - Treat as error → fallback.
   - **Otherwise:**
     - Proceed to Execution (Segment 4) and call that agent.

---

## 7. Fallback Behaviour (Routing-level)

If routing decides no agent should be used (`selected_agent = "none"`) or returns an invalid agent:

**AgentHost can:**

- **Option A:** Ask LLM directly to answer the user query (no agents).
- **Option B:** Return a friendly "I'm not capable of handling this request yet."

The exact fallback behaviour is controlled at a higher level (we'll detail when we design the overall flow).

---

## 8. What to add to README from this segment

In your README, under **"LLM-Based Routing"**, you can capture:

### Routing Modes

AgentHost supports two routing modes:

- **`auto`** – LLM selects the best agent.
- **`manual`** – user explicitly chooses an agent; routing is skipped.

### In `auto` mode, AgentHost:

1. Sends `user_query` + a condensed list of agents (name, description, tags, curated prompts, examples) to an LLM router.
2. The LLM returns `selected_agent`, `confidence`, and `reasoning`.
3. AgentHost either:
   - Calls that agent, or
   - Falls back if `selected_agent = "none"` or invalid.

### In `manual` mode, AgentHost:

- Directly calls the `selected_agent` if it exists in the registry.

---

## ✅ Segment 3 is Now Designed

We have a clear routing mechanism that supports both intelligent auto-routing via LLM and explicit manual agent selection.
