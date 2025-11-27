import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="LiteLLM Chat",
    page_icon="🤖",
    layout="wide"
)

# Initialize OpenAI client
@st.cache_resource
def get_client():
    return OpenAI(
        base_url=os.getenv("LITELLM_BASE_URL", "http://localhost:4100/v1"),
        api_key=os.getenv("LITELLM_API_KEY", "sk-litellm-hub-local-123")
    )

client = get_client()

# Fetch available models
@st.cache_data(ttl=60)
def get_available_models():
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return ["tinyllama", "qwen2.5", "phi"]  # Fallback

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "tinyllama"

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Model selection
    available_models = get_available_models()
    selected_model = st.selectbox(
        "Select Model",
        options=available_models,
        index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
        help="Choose which LLM model to use for chat"
    )
    st.session_state.selected_model = selected_model
    
    # Model info
    model_info = {
        "tinyllama": {"size": "637 MB", "speed": "⚡⚡⚡"},
        "qwen2.5": {"size": "397 MB", "speed": "⚡⚡⚡"},
        "phi": {"size": "1.6 GB", "speed": "⚡⚡"}
    }
    
    if selected_model in model_info:
        st.info(f"**Size:** {model_info[selected_model]['size']}\n\n**Speed:** {model_info[selected_model]['speed']}")
    
    st.divider()
    
    # Temperature slider
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more random"
    )
    
    # Max tokens
    max_tokens = st.slider(
        "Max Tokens",
        min_value=50,
        max_value=2000,
        value=500,
        step=50,
        help="Maximum length of response"
    )
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    # Connection status
    st.divider()
    st.caption("🟢 Connected to LiteLLM Hub")
    st.caption(f"�� {os.getenv('LITELLM_BASE_URL', 'http://localhost:4100/v1')}")

# Main chat interface
st.title("🤖 LiteLLM Chat Interface")
st.caption(f"Currently using: **{selected_model}**")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Stream the response
            stream = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            full_response = error_msg
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Footer
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Messages", len(st.session_state.messages))
with col2:
    st.metric("Model", selected_model)
with col3:
    st.metric("Temp", f"{temperature:.1f}")
