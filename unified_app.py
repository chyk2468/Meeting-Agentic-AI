import streamlit as st
import os
import json
import sys
from dotenv import load_dotenv
from groq import Groq

# Add subdirectories to path to reuse existing modules
sys.path.append(os.path.join(os.getcwd(), "gc agent"))
sys.path.append(os.path.join(os.getcwd(), "Jira AI Agent"))

# Import existing handlers and clients
try:
    from actions import ActionHandler as CalendarHandler
    import jira_client
    from actions import dispatch as jira_dispatch
    from vector_store import sync_project_issues
except ImportError as e:
    st.error(f"Mapping error: {e}. Ensure you run this from the project root.")

load_dotenv("gc agent/.env") # Load common keys from one of the .env files

st.set_page_config(page_title="Master AI Agent", page_icon="🧠", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .stCard {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #58a6ff; }
</style>
""", unsafe_allow_html=True)

# --- Logic ---
class MasterAgent:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.prompt_template = """
You are an intelligent Task and Event Extraction Agent.
Your job is to analyze raw user input (such as meeting transcripts, notes, or conversations) and extract two categories of actionable items:

1. Project-related tasks → for Jira Agent
2. Time-based events/reminders → for Google Calendar Agent

---
OUTPUT FORMAT (STRICT JSON ONLY):
{
"jira_tasks": [
{
"title": "string",
"description": "string",
"priority": "low | medium | high",
"assignee": "string or null",
"due_date": "YYYY-MM-DD or null"
}
],
"calendar_events": [
{
"title": "string",
"datetime": "YYYY-MM-DD HH:MM",
"duration_minutes": integer,
"participants": ["list of names"],
"description": "string"
}
]
}

---
EXTRACTION RULES:
JIRA TASKS:
* Include development work, bugs, features, assignments, or deliverables
* Infer priority:
  * urgent / ASAP → high
  * near deadline → medium
  * normal → low

CALENDAR EVENTS:
* Include meetings, calls, discussions, reminders, and important dates
* If duration is not specified, assume 30 minutes

---
IMPORTANT:
* Do NOT mix tasks and events
* Do NOT hallucinate missing information
* If date/time is missing → use null
* If assignee is not mentioned → use null
* If participants are not mentioned → use empty list []
* If both task and meeting exist in one sentence → split into both
"""

    def parse_input(self, user_input):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

# --- UI ---
st.title("🧠 Master Task & Event Agent")
st.markdown("Paste meeting transcripts or notes below to automatically route tasks to Jira and events to Google Calendar.")

with st.sidebar:
    st.header("⚙️ Configuration")
    groq_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
    
    st.divider()
    st.subheader("Jira Settings")
    j_email = st.text_input("Jira Email", value=os.getenv("JIRA_EMAIL", ""))
    j_token = st.text_input("Jira API Token", type="password", value=os.getenv("JIRA_API_KEY", ""))
    j_domain = st.text_input("Jira Domain", value=os.getenv("JIRA_DOMAIN", ""))
    j_project = st.text_input("Default Project Key", value="PROJ")

if not groq_key:
    st.warning("Please enter your Groq API Key in the sidebar.")
    st.stop()

agent = MasterAgent(groq_key)

raw_input = st.text_area("📋 Raw Input (Transcript/Notes)", height=250, placeholder="Example: Meeting with Yash today at 5pm to discuss the login bug. Yash needs to fix the CSS issues by Friday ASAP.")

if st.button("🚀 Process & Extract", use_container_width=True):
    if raw_input:
        with st.spinner("Analyzing and extracting..."):
            extracted = agent.parse_input(raw_input)
            st.session_state.extracted_data = extracted
            st.rerun()

if "extracted_data" in st.session_state:
    data = st.session_state.extracted_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🎫 Jira Tasks")
        tasks = data.get("jira_tasks", [])
        if not tasks:
            st.info("No Jira tasks detected.")
        for i, task in enumerate(tasks):
            with st.container():
                st.markdown(f"### {task['title']}")
                st.write(f"**Priority:** {task['priority'].upper()}")
                st.write(f"**Description:** {task['description']}")
                if st.button(f"Push to Jira", key=f"jira_{i}"):
                    # Map to Jira Agent format
                    params = {
                        "summary": task['title'],
                        "description": task['description'],
                        "priority": task['priority'].capitalize(),
                        "issuetype": "Task"
                    }
                    if task.get('due_date'): params["due_date"] = task['due_date']
                    
                    try:
                        res = jira_dispatch("create_issue", params, j_domain, j_email, j_token, j_project)
                        st.success(f"Success!")
                        st.markdown(res)
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        st.header("📅 Calendar Events")
        events = data.get("calendar_events", [])
        if not events:
            st.info("No calendar events detected.")
        for i, event in enumerate(events):
            with st.container():
                st.markdown(f"### {event['title']}")
                st.write(f"**Time:** {event['datetime']}")
                st.write(f"**Participants:** {', '.join(event['participants']) if event['participants'] else 'None'}")
                if st.button(f"Add to Calendar", key=f"cal_{i}"):
                    try:
                        # Re-init handler to ensure fresh auth
                        handler = CalendarHandler()
                        action = {
                            "action": "create_event",
                            "title": event['title'],
                            "time": event['datetime']
                        }
                        res = handler.execute(action)
                        st.success(res)
                    except Exception as e:
                        st.error(f"Error: {e}")

    if st.button("Clear Results"):
        del st.session_state.extracted_data
        st.rerun()
