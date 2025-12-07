# Segment 2 – Registration & Deregistration Contract

## Goal of this Segment

Define how an independent agent talks to AgentHost to say:
- **"I exist, here are my details."** and later
- **"I'm going away, remove me."**

This is the protocol, based on the registry fields we defined in Segment 1.

---

## 1️⃣ Registration – High-Level Flow

Think of what happens when an agent (e.g., DevOpsAgent) starts:

1. **Agent starts up.**

2. **Agent prepares its identity** + capabilities + curated prompts + examples + how_to_call.

3. **Agent sends a Register Request to AgentHost.**

4. **AgentHost:**
   - Validates the data.
   - Stores/updates the entry in the Agent Registry.
   - Marks it as `health_status = "healthy"` (initially).
   - Returns a Register Response with status + assigned `agent_id` (if you want one separate from `agent_name`).

5. **Agent logs** "registered successfully" or handles failure.

### Design Requirements

From a design point of view, we need to define:

- What's inside the **Register Request**
- What's inside the **Register Response**

---

## 2️⃣ Register Request – Payload Design

Conceptually, a Register Request contains everything we defined in Segment 1 (except `health_status`, which AgentHost manages).

Let's define it as a conceptual object:

```yaml
RegisterRequest:
  agent_name: string
  description: string
  capability_tags: [string]
  curated_routing_prompts: string
  example_queries: [string]
  usage_hints: string (optional)
  how_to_call: string or structured object
  version: string (optional)
```

### Field Meanings (Quick Recap)

#### `agent_name`
Unique across the system (e.g., `"DevOpsAgent"`).

#### `description`
Human-readable purpose, 1–2 lines.

#### `capability_tags`
Keywords like `["azure", "github", "costs", "runners"]`.

#### `curated_routing_prompts`
Text telling LLM router when to choose this agent.

#### `example_queries`
3–5 real-world queries where this agent is ideal.

#### `usage_hints` (optional)
How LLM should explain/format the results coming from this agent.

#### `how_to_call`
Info needed by AgentHost to invoke this agent (could be `"http://…"` or internal handler id).

#### `version` (optional)
Agent's own version string.

### 🔑 Design Rule

**Registration must be idempotent** — if the same agent calls register again with updated info, AgentHost simply updates the registry entry.

---

## 3️⃣ Register Response – Payload Design

After processing the request, AgentHost replies with a Register Response:

```yaml
RegisterResponse:
  status: "success" | "error"
  agent_name: string
  agent_id: string (optional, assigned by AgentHost)
  message: string
  errors: [string] (optional, only if status = "error")
```

### Behaviour

#### If everything is valid:

- `status = "success"`
- `agent_name` echoed back
- `agent_id` can be same as `agent_name` or an internal UUID
- `message` e.g., `"Agent registered successfully."`

#### If validation fails (missing fields, bad data):

- `status = "error"`
- `errors` list with reasons, e.g.:
  - `"agent_name is required"`
  - `"example_queries must not be empty"`

This gives agents clear feedback and supports robust workflows.

---

## 4️⃣ Deregistration – High-Level Flow

When an agent wants to shut down gracefully:

1. **Agent prepares a Deregister Request.**

2. **Agent sends it to AgentHost.**

3. **AgentHost:**
   - Removes or marks the agent as disabled/unavailable.
   - Returns Deregister Response.

This prevents AgentHost from routing queries to a dead agent.

---

## 5️⃣ Deregister Request – Payload Design

We keep this minimal and clear:

```yaml
DeregisterRequest:
  agent_name: string
  reason: string (optional)
```

### Fields

#### `agent_name`
Identifies which agent to deregister (must match registered name).

#### `reason` (optional)
For logs/observability, e.g.:
- `"shutdown"`
- `"deploying new version"`
- `"maintenance"`

---

## 6️⃣ Deregister Response – Payload Design

```yaml
DeregisterResponse:
  status: "success" | "error"
  agent_name: string
  message: string
  errors: [string] (optional)
```

### Examples

#### On success:

- `status: "success"`
- `message: "Agent deregistered successfully."`

#### On error:

- `status: "error"`
- `errors: ["agent_name not found in registry"]`

---

## 7️⃣ Error & Edge-Case Behaviour (Design Decisions)

These are important small rules that make the system predictable:

### Re-registering the same agent

- If `agent_name` already exists, `RegisterRequest` updates the existing entry.
- This supports rolling updates or config changes.

### Deregistering a non-existent agent

- Returns `status = "error"` with a clear message.
- Useful to catch bugs in agent lifecycle logic.

### Partial registrations (missing fields)

- AgentHost should treat missing required fields as error.
- Optional fields can be left blank.

### Health management

- Registration automatically implies `health_status = "healthy"`.
- Deregistration removes or marks agent as `health_status = "unavailable"`.

---

## 8️⃣ How this fits into README (what you can add now)

You can now add a new section to your `README.md`:

### Agent Registration & Deregistration (High-Level Contract)

**Summarize:**

- **Agents call AgentHost with a `RegisterRequest` containing:**
  - `agent_name`, `description`, `capability_tags`, `curated_routing_prompts`, `example_queries`, `usage_hints`, `how_to_call`, `version`.

- **AgentHost replies with `RegisterResponse`:**
  - `status`, `agent_name`, `agent_id`, `message`, `errors`.

- **For shutdown, agents send `DeregisterRequest`:**
  - `agent_name`, `reason`.

- **AgentHost replies with `DeregisterResponse`:**
  - `status`, `agent_name`, `message`, `errors`.

No JSON, no code — just text explanation of these structures.

---

## ✅ Segment 2 is Now Designed

We know what registration/deregistration look like and how agents and AgentHost talk at a high level.
