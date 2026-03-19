import streamlit as st
import os
from agent import CalendarAgent
from actions import ActionHandler
from dotenv import load_dotenv

# Page config
st.set_page_config(page_title="Google Calendar AI Assistant", page_icon="📅", layout="centered")

# Custom CSS for premium feel
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatFloatingInputContainer {
        border-bottom: 1px solid #ddd;
    }
    h1 {
        color: #1a73e8;
    }
    </style>
""", unsafe_allow_html=True)

# App title
st.title("📅 Google Calendar AI")
st.subheader("Your AI-powered Scheduling Assistant")

# Check for .env and credentials.json
if not os.path.exists('.env'):
    st.error("⚠️ `.env` file not found. Please create one with `GROQ_API_KEY`.")
    st.stop()

if not os.path.exists('credentials.json'):
    st.error("⚠️ `credentials.json` not found. Please provide it for OAuth flow.")
    st.info("Download it from: https://console.cloud.google.com/apis/credentials")
    st.stop()

# Initialize session state for agent, handler, chat history, and pending actions
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_actions" not in st.session_state:
    st.session_state.pending_actions = []

if "agent" not in st.session_state:
    try:
        st.session_state.agent = CalendarAgent()
        st.session_state.handler = ActionHandler()
    except Exception as e:
        st.error(f"Error initializing AI: {e}")
        st.stop()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Pending Actions Confirmation UI
if st.session_state.pending_actions:
    with st.chat_message("assistant"):
        st.write("📋 **I found the following events. Should I add them to your calendar?**")
        
        for i, action in enumerate(st.session_state.pending_actions):
            col1, col2 = st.columns([0.1, 0.9])
            with col2:
                st.info(f"**{action.get('title')}**\n\n🕒 {action.get('time')}")
        
        col_c, col_x = st.columns(2)
        if col_c.button("✅ Confirm All", use_container_width=True):
            with st.status("Uploading to calendar...", expanded=True) as status:
                results = []
                for action in st.session_state.pending_actions:
                    res = st.session_state.handler.execute(action)
                    results.append(res)
                
                final_msg = "\n".join(results)
                status.update(label="Complete!", state="complete")
                st.markdown(final_msg)
                st.session_state.messages.append({"role": "assistant", "content": f"Batch upload complete:\n{final_msg}"})
                st.session_state.pending_actions = []
                st.rerun()
                
        if col_x.button("❌ Cancel", use_container_width=True):
            st.session_state.pending_actions = []
            st.session_state.messages.append({"role": "assistant", "content": "Operation cancelled."})
            st.rerun()

# User Input
if prompt := st.chat_input("How can I help with your calendar today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process AI action
    with st.chat_message("assistant"):
        with st.status("Analyzing...", expanded=False) as status:
            try:
                # 1. Get structured actions from AI
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
                response_json = st.session_state.agent.get_action(prompt, history_text)
                actions = response_json.get("actions", [])
                
                if not actions:
                    st.write("I'm not sure what to do. Could you clarify?")
                    st.session_state.messages.append({"role": "assistant", "content": "I'm not sure what to do. Could you clarify?"})
                else:
                    # 2. Check if we have multiple events to create or if user wants confirmation
                    create_actions = [a for a in actions if a.get("action") == "create_event"]
                    other_actions = [a for a in actions if a.get("action") != "create_event"]
                    
                    # If there are create actions, move them to pending
                    if create_actions:
                        st.session_state.pending_actions = create_actions
                        status.update(label="Ready for confirmation", state="complete")
                        st.write(f"I've prepared {len(create_actions)} event(s). Please review them above.")
                        st.rerun()
                    
                    # Execute other actions immediately (like list_events)
                    for action in other_actions:
                        status.update(label=f"Executing: {action.get('action')}", state="running")
                        response_text = st.session_state.handler.execute(action)
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    status.update(label="Complete!", state="complete")
            except Exception as e:
                error_msg = f"Sorry, something went wrong: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar Sidebar Info
with st.sidebar:
    st.write("### Instructions")
    st.write("- **List events**: 'Show upcoming events'")
    st.write("- **Create event**: 'Meeting with HR tomorrow at 2 PM'")
    st.write("- **Delete event**: 'Delete that HR meeting'")
    
    if st.button("Reset Chat History"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.info("Note: Your token expires and refreshes automatically via `token.json`.")
