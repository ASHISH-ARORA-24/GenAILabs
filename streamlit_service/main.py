import streamlit as st
import requests
from typing import List, Dict, Any

# ===========================
# Config (adjust if needed)
# ===========================

DEFAULT_AGENTHOST_URL = "http://localhost:8000"
DEFAULT_LITELLM_URL = "http://localhost:4100"
DEFAULT_LITELLM_API_KEY = "sk-litellm-hub-local-123"


# ===========================
# Helper functions
# ===========================

def get_agenthost_base_url() -> str:
    return st.session_state.get("agenthost_url", DEFAULT_AGENTHOST_URL).rstrip("/")


def get_litellm_base_url() -> str:
    return st.session_state.get("litellm_url", DEFAULT_LITELLM_URL).rstrip("/")


def get_litellm_api_key() -> str:
    return st.session_state.get("litellm_api_key", DEFAULT_LITELLM_API_KEY)


@st.cache_data(show_spinner=False)
def fetch_agents(agenthost_url: str) -> List[Dict[str, Any]]:
    try:
        resp = requests.get(f"{agenthost_url}/agenthost/agents", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("agents", [])
    except Exception as e:
        st.error(f"Error fetching agents from AgentHost: {e}")
        return []


@st.cache_data(show_spinner=False)
def fetch_llm_models(agenthost_url: str) -> List[str]:
    """
    Uses AgentHost endpoint /agenthost/llm-models,
    which internally calls LiteLLM /v1/models.
    """
    try:
        resp = requests.get(f"{agenthost_url}/agenthost/llm-models", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Expecting LiteLLM-like structure: { "data": [ {"id": "..."} ] }
        models = []
        for item in data.get("data", []):
            model_id = item.get("id")
            if model_id:
                models.append(model_id)
        return models
    except Exception as e:
        st.error(f"Error fetching LLM models: {e}")
        return []


def call_agenthost_query(
    agenthost_url: str,
    user_query: str,
    routing_mode: str,
    selected_agent: str | None,
) -> str:
    payload = {
        "user_query": user_query,
        "routing_mode": routing_mode,
        "selected_agent": selected_agent,
    }
    try:
        resp = requests.post(
            f"{agenthost_url}/agenthost/query",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("reply", "(no reply field)")
    except Exception as e:
        return f"[AgentHost error] {e}"


def call_direct_llm_chat(
    litellm_url: str,
    api_key: str,
    model: str,
    user_query: str,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Simple direct chat with LiteLLM /v1/chat/completions
    history: list of {"role": "user"/"assistant", "content": "..."}
    """
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 256,
    }

    try:
        resp = requests.post(
            f"{litellm_url}/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LiteLLM error] {e}"


# ===========================
# Streamlit UI
# ===========================

st.set_page_config(page_title="GenAILab AgentHost UI", layout="wide")

st.title("🧠 GenAILab – AgentHost & LLM Chat")

with st.sidebar:
    st.header("⚙️ Configuration")

    agenthost_url = st.text_input(
        "AgentHost URL",
        value=st.session_state.get("agenthost_url", DEFAULT_AGENTHOST_URL),
        help="Base URL of FastAPI AgentHost service",
    )
    st.session_state["agenthost_url"] = agenthost_url

    litellm_url = st.text_input(
        "LiteLLM URL",
        value=st.session_state.get("litellm_url", DEFAULT_LITELLM_URL),
        help="Base URL of LiteLLM proxy",
    )
    st.session_state["litellm_url"] = litellm_url

    litellm_api_key = st.text_input(
        "LiteLLM API Key",
        value=st.session_state.get("litellm_api_key", DEFAULT_LITELLM_API_KEY),
        help="API key used to call LiteLLM",
        type="password",
    )
    st.session_state["litellm_api_key"] = litellm_api_key

    st.markdown("---")
    if st.button("🔄 Refresh Agents & LLM Models"):
        fetch_agents.clear()
        fetch_llm_models.clear()
        st.rerun()

# Load agents & models
agents = fetch_agents(get_agenthost_base_url())
agent_names = [a["agent_name"] for a in agents]

llm_models = fetch_llm_models(get_agenthost_base_url())

# Session state for chat history
if "agenthost_history" not in st.session_state:
    st.session_state["agenthost_history"] = []  # list of (role, content)
if "llm_history" not in st.session_state:
    st.session_state["llm_history"] = []       # list of {"role": "...", "content": "..."}

tab_agenthost, tab_llm = st.tabs(["🤖 AgentHost Chat", "🧩 Direct LLM Chat"])

# ===========================
# TAB 1: AgentHost Chat
# ===========================

with tab_agenthost:
    st.subheader("🤖 AgentHost Chat (Agents + Routing + Composer)")

    # Agent selection
    agent_options = ["Any (auto)"] + agent_names
    selected_agent_option = st.selectbox(
        "Select Agent",
        options=agent_options,
        help="Choose 'Any (auto)' to let AgentHost decide, or pick a specific agent (manual mode).",
    )

    if selected_agent_option == "Any (auto)":
        routing_mode = "auto"
        selected_agent_value = None
    else:
        routing_mode = "manual"
        selected_agent_value = selected_agent_option

    user_input = st.text_input(
        "Your message",
        key="agenthost_input",
        placeholder="Ask something for AgentHost...",
    )

    if st.button("Send to AgentHost", key="send_agenthost"):
        if user_input.strip():
            # Call AgentHost
            reply = call_agenthost_query(
                get_agenthost_base_url(),
                user_input.strip(),
                routing_mode,
                selected_agent_value,
            )

            # Update history
            st.session_state["agenthost_history"].append(("user", user_input.strip()))
            st.session_state["agenthost_history"].append(("assistant", reply))

    st.markdown("### Conversation")
    for role, content in st.session_state["agenthost_history"]:
        if role == "user":
            st.markdown(f"**You:** {content}")
        else:
            st.markdown(f"**AgentHost:** {content}")


# ===========================
# TAB 2: Direct LLM Chat
# ===========================

with tab_llm:
    st.subheader("🧩 Direct LLM Chat (LiteLLM)")

    if llm_models:
        selected_model = st.selectbox(
            "Select LLM model",
            options=llm_models,
            help="Models fetched via AgentHost → LiteLLM /v1/models.",
        )
    else:
        st.warning("No LLM models found via AgentHost. Using manual entry.")
        selected_model = st.text_input("LLM model ID", value="tinyllama")

    user_input_llm = st.text_input(
        "Your message (Direct LLM)",
        key="llm_input",
        placeholder="Talk directly to a specific model...",
    )

    if st.button("Send to LLM", key="send_llm"):
        if user_input_llm.strip():
            # Prepare history in chat-completions format
            history_for_model = st.session_state["llm_history"]
            reply = call_direct_llm_chat(
                get_litellm_base_url(),
                get_litellm_api_key(),
                selected_model,
                user_input_llm.strip(),
                history_for_model,
            )

            # Update history (for model context)
            st.session_state["llm_history"].append(
                {"role": "user", "content": user_input_llm.strip()}
            )
            st.session_state["llm_history"].append(
                {"role": "assistant", "content": reply}
            )

    st.markdown("### Conversation")
    for msg in st.session_state["llm_history"]:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**LLM ({selected_model}):** {msg['content']}")
