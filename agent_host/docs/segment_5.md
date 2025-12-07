# Segment 5 – Final Response Composer (LLM-based Answer Builder)

## 1. Purpose

Once an agent has done its work, we have:

- Raw or structured result (JSON, numbers, text, etc.)
- Original user query
- Agent metadata (name, description, usage hints)

The **Final Response Composer** is an LLM call that:

```
Takes raw agent result + context
→ Produces a clear, friendly, user-facing answer for Streamlit.
```

This keeps agents technical and the composer human-friendly.

---

## 2. Inputs to the Composer

AgentHost will call the composer LLM with a structured input:

```yaml
ComposerInput:
  user_query: string
  selected_agent: string
  agent_description: string
  usage_hints: string (optional)
  execution_status: "success" | "error" | "partial"
  execution_result: object | string
  execution_error: string (optional)
```

### Field meanings:

#### `user_query`
What the user originally asked.

#### `selected_agent`
The agent that produced the result (`"DevOpsAgent"`, `"RAGAgent"`, etc.).

#### `agent_description`
From registry — helps LLM know what data it's looking at.

#### `usage_hints`
From registry — e.g.,
```
"Always explain cost impact and next actions in plain language."
```

#### `execution_status`

- `"success"` → normal flow
- `"error"` → we need a graceful error explanation
- `"partial"` → explain what was done and what's missing

#### `execution_result`
Raw output from agent (`result` field of `ExecutionResponse`).

#### `execution_error`
Only used if `status = "error"`.

---

## 3. Prompt Structure for Composer LLM

Like the router, composer uses:

1. **System message** – define behaviour & style
2. **Context message** – give agent info + raw result
3. **User message** – original query

### 3.1 System message (role)

**Conceptual content:**

```
You are a response formatter.

Use:
- user's question
- agent's description
- execution result
- usage hints

Produce:
- A helpful answer in clear, simple language.
- Short where possible, detailed when needed.

If execution_status = "error":
- Explain limitation politely.
- Use execution_error to describe what went wrong.

Do not invent data that isn't present in result.
```

### 3.2 Context message

Contains:
- Agent name + description
- Execution status
- Raw result / error
- Usage hints

**Concept example:**

```
Agent used: DevOpsAgent
Agent description: Handles Azure, GitHub runners, CI/CD infrastructure, and cloud cost insights.

Execution status: success

Raw result from agent:
{
  "vm_costs_last_7_days": 74.33,
  "trend": "increasing",
  "recommendation": "scale down 1 runner"
}

Usage hints from agent:
- Always mention the time range.
- Explain cost impact in simple English.
- Provide 1–3 concrete next steps.
```

### 3.3 User message

**Example:**

```
User query:
"Check Azure VM costs for RunnerScale for last 7 days and tell me if we overspent."
```

---

## 4. Composer Output Schema (what we expect from LLM)

Even if we show only text to the user, it's useful to design a structure:

```yaml
ComposerOutput:
  final_answer: string
  short_summary: string (optional)
  reasoning: string (optional, internal/log)
```

You can start by using only `final_answer`.

The others (`short_summary`, `reasoning`) are nice later for logs or UI.

### Example:

#### `final_answer`:
```
"In the last 7 days, your Azure VM costs for RunnerScale were approximately $74.33 and are trending upward. This suggests a mild overspend compared to a stable baseline.

Recommended actions:
1. Scale down one GitHub runner VM during low-traffic hours.
2. Review idle VM time and consider auto-shutdown.
3. Re-check costs after another week to confirm improvement."
```

#### `short_summary`:
```
"Costs are increasing slightly; scale down 1 runner and monitor."
```

---

## 5. Behaviour for Different `execution_status`

### 5.1 `status = "success"`

**LLM:**
- Answers the user query.
- Uses agent's `usage_hints` for style & structure.
- Can summarise, prioritize, and explain.

### 5.2 `status = "partial"`

**LLM:**
- Clearly say what info was found.
- Clearly say what couldn't be done.
- Suggest next steps (e.g., "try again later", "narrow the query").

**Example:**
```
"I could fetch cost data for only 3 of the last 7 days due to API limits…"
```

### 5.3 `status = "error"`

**LLM:**
- Apologizes gently.
- Uses `execution_error` to explain in safe language.
- Does not fabricate successful results.
- Optionally, gives suggestions:
  - "Try again later"
  - "Contact admin"
  - "Narrow query"

**Example:**
```
"DevOpsAgent could not fetch Azure VM cost data because the Azure API timed out. I don't have enough data to answer your question right now. Please try again later or check Azure Cost Management directly."
```

---

## 6. Where Composer Sits in the Flow

Full flow recap with the composer:

1. **Streamlit → AgentHost:** user query + `routing_mode`.

2. **AgentHost:**
   - Decides agent (router or manual).
   - Builds `ExecutionRequest`.

3. **Agent → `ExecutionResponse`** (success/partial/error).

4. **AgentHost builds `ComposerInput`.**

5. **AgentHost → Composer LLM.**

6. **Composer LLM → `ComposerOutput.final_answer`.**

7. **AgentHost → Streamlit:** final answer.

### Summary:
- **Router** decides who works,
- **Agent** does the work,
- **Composer** decides how to explain it.

---

## 7. README Section for Segment 5

You can add:

### Final Response Composer (LLM-Based Answer Formatting)

**Key bullets:**

#### Composer takes:
- `user_query`
- `selected_agent`
- `agent_description`
- `usage_hints`
- `execution_status`
- `execution_result` / `execution_error`

#### Builds a prompt with:
- **System:** "You are a formatter…"
- **Context:** agent info + raw result
- **User:** original query

#### LLM returns:
- `final_answer` (required)
- optional `short_summary` / `reasoning`.

#### Handles:
- **success** → normal explanation
- **partial** → "here's what I could do"
- **error** → graceful failure message.

---

## ✅ Segment 5 is Now Designed

We have a clear final response composition strategy that transforms raw agent outputs into polished, user-friendly answers.
