import streamlit as st
import os
import json
import sys
import importlib.util
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Function to safely load a module to avoid Streamlit rerun issues and name collisions
def load_module(module_name, file_path):
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Add subdirectories to path
sys.path.append(os.path.join(os.getcwd(), "gc agent"))
sys.path.append(os.path.join(os.getcwd(), "Jira AI Agent"))

try:
    calendar_actions = load_module("calendar_actions", os.path.join("gc agent", "actions.py"))
    jira_actions = load_module("jira_actions", os.path.join("Jira AI Agent", "actions.py"))
    jira_agent_module = load_module("jira_agent", os.path.join("Jira AI Agent", "agent.py"))
    calendar_agent_module = load_module("calendar_agent", os.path.join("gc agent", "agent.py"))
    
    CalendarHandler = calendar_actions.ActionHandler
    jira_dispatch = jira_actions.dispatch
    jira_parse = jira_agent_module.parse_task
    CalendarAgent = calendar_agent_module.CalendarAgent
except Exception as e:
    st.error(f"Import Error: {e}. Ensure you are in the project root directory.")
    st.stop()

# Load environment variables from both sub-agents
load_dotenv(os.path.join("gc agent", ".env"))
load_dotenv(os.path.join("Jira AI Agent", ".env"))

st.set_page_config(page_title="Nexus AI Master", page_icon="🧠", layout="wide")

# Verify Google Calendar Credentials path
GC_CREDS_PATH = os.path.join(os.getcwd(), "gc agent", "credentials.json")
if not os.path.exists(GC_CREDS_PATH):
    st.error(f"⚠️ **Google Calendar Error:** `credentials.json` not found at `{GC_CREDS_PATH}`.")
    st.info("Please place your Google Cloud credentials file in the 'gc agent' folder.")

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

import logging

# Configure Audit Logger
logging.basicConfig(
    filename='nexus_audit.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

def audit_log(action, status, details):
    logging.info(f"ACTION: {action} | STATUS: {status} | DETAILS: {details}")

class RouterAgent:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.prompt_template = """
SYSTEM: NEXUS AI — CONVERSATIONAL AGENTIC ROUTER

You are NexusAI, a conversational agentic AI system.
You behave like a natural chatbot for the user, BUT internally you are a router and orchestrator that decides which specialized agent to use:
* Jira Agent → for tasks, bugs, project updates, assignments
* Google Calendar Agent → for meetings, schedules, events
* Task Extraction Mode → for long transcripts or notes

---
🧠 CORE BEHAVIOR
1. Understand user intent from natural conversation
2. Decide the correct mode:

MODES:
* "chat" → normal conversation
* "jira_query" → ask Jira Agent directly
* "calendar_query" → ask Calendar Agent directly
* "extraction" → run full task + event extraction pipeline

---
⚙️ ROUTING RULES
👉 Use "calendar_query" IF user asks:
* upcoming meetings
* schedule
* events
* availability
* reminders

👉 Use "jira_query" IF user asks:
* project status
* bugs
* tasks
* tickets
* assignments
* progress updates

👉 Use "extraction" IF input is:
* long paragraph
* meeting transcript
* multiple actions mixed

👉 Otherwise:
* use "chat"

---
📤 OUTPUT FORMAT (STRICT JSON ONLY)
{
"mode": "chat | jira_query | calendar_query | extraction",
"response": "natural language reply to user",
"agent_payload": {
"query": "string (for jira/calendar agent)",
"filters": {}
}
}
"""

    def route(self, user_input):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt_template},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_response = completion.choices[0].message.content
            audit_log("ROUTER", "SUCCESS", f"Mode determined: {json.loads(raw_response).get('mode')}")
            return json.loads(raw_response)
        except Exception as e:
            audit_log("ROUTER", "FAILED", str(e))
            return {"mode": "chat", "response": f"Error in routing: {str(e)}", "agent_payload": {}}

class MasterAgent:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.prompt_template = """
SYSTEM: NEXUS AI — MASTER ORCHESTRATOR AGENT

You are NexusAI, a fully autonomous, agentic AI orchestration system.
You are NOT a chatbot. You are a self-driving workflow engine.

---
🧠 STEP 1: UNDERSTAND & PLAN (COGNITIVE LAYER)
Analyze input, produce intent summary, and identify Jira Tasks vs Calendar Events.

⚙️ STEP 2: DECIDE EXECUTION (DECISION LAYER)
Set "auto_execute": true/false and "requires_clarification": true/false. Generate questions if needed.

📦 STEP 3: STRUCTURED EXTRACTION (TASK AGENT OUTPUT)
Generate "jira_packet" and "calendar_packet".

📊 STEP 4: CONFIDENCE SCORING
Assign confidence 0.0 to 1.0 to each item.

🔁 STEP 5: SELF-REFLECTION
Detect missed tasks or events.

---
OUTPUT FORMAT (STRICT JSON ONLY):
{
"plan": {
"summary": "string",
"requires_clarification": false,
"auto_execute": true
},
"jira_packet": [
{
"title": "string",
"description": "string",
"priority": "low | medium | high",
"assignee": "string or null",
"due_date": "YYYY-MM-DD or null",
"confidence": 0.0
}
],
"calendar_packet": [
{
"title": "string",
"datetime": "YYYY-MM-DD HH:MM or null",
"duration_minutes": 30,
"participants": [],
"description": "string",
"confidence": 0.0
}
],
"reflection": {
"missed_items": []
},
"clarification_questions": []
}

---
📌 RULES:
* NEVER mix tasks and events.
* Default duration = 30 mins.
* Split combined sentences.
* Priority: HIGH (ASAP), MEDIUM (Deadline), LOW (General).
"""

    def parse_input(self, user_input):
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt_template},
                    {"role": "user", "content": f"Context: Today's date is {current_date}.\n\nInput: {user_input}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_response = completion.choices[0].message.content
            audit_log("PARSE_INPUT", "SUCCESS", f"Input length: {len(user_input)}")
            return json.loads(raw_response)
        except Exception as e:
            audit_log("PARSE_INPUT", "FAILED", str(e))
            return {"error": str(e)}

st.title("🚀 Nexus AI: Master Orchestrator")
st.markdown("Autonomous Workflow Engine for Jira & Calendar")

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
router = RouterAgent(groq_key)

raw_input = st.text_area("💬 Conversational Input", height=150, placeholder="Ask me anything, or paste a transcript for extraction...")

if st.button("🚀 Send to Nexus", use_container_width=True):
    if raw_input.strip():
        with st.spinner("Nexus is routing your request..."):
            route_data = router.route(raw_input)
            st.session_state.route_data = route_data
            
            mode = route_data.get("mode", "chat")
            
            if mode == "extraction":
                with st.spinner("Running deep extraction..."):
                    extracted = agent.parse_input(raw_input)
                    if "error" in extracted:
                        st.error(f"Extraction Error: {extracted['error']}")
                    else:
                        st.session_state.extracted_data = extracted
                        st.session_state.execution_results = []
                        st.rerun()
            
            elif mode == "jira_query":
                with st.spinner("Consulting Jira Agent..."):
                    query = route_data.get("agent_payload", {}).get("query", raw_input)
                    # We can use jira_parse to get actions and then execute them
                    actions = jira_parse(query, groq_key)
                    results = []
                    for action in actions:
                        res = jira_dispatch(action['action'], action['params'], j_domain, j_email, j_token, j_project)
                        results.append(res)
                    st.session_state.query_results = results
                    st.rerun()
                    
            elif mode == "calendar_query":
                with st.spinner("Consulting Calendar Agent..."):
                    query = route_data.get("agent_payload", {}).get("query", raw_input)
                    cal_agent = CalendarAgent()
                    actions_json = cal_agent.get_action(query)
                    handler = CalendarHandler()
                    results = []
                    for action in actions_json.get("actions", []):
                        res = handler.execute(action)
                        results.append(res)
                    st.session_state.query_results = results
                    st.rerun()

# --- Display Results ---

if "route_data" in st.session_state:
    route = st.session_state.route_data
    if route['mode'] != "extraction":
        st.chat_message("assistant").write(route.get("response", "Processing your request..."))
        
        if "query_results" in st.session_state:
            for res in st.session_state.query_results:
                st.info(res)
        
        if st.button("Clear Conversation"):
            del st.session_state.route_data
            if "query_results" in st.session_state: del st.session_state.query_results
            st.rerun()

if "extracted_data" in st.session_state:
    data = st.session_state.extracted_data
    plan = data.get("plan", {})
    
    # --- Planning & Reflection Section ---
    with st.expander("📝 **Agent's Internal Plan & Reflection**", expanded=True):
        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            st.write(f"**Summary:** {plan.get('summary', 'No summary provided.')}")
            if data.get("clarification_questions"):
                st.warning("❓ **Clarification Needed:**")
                for q in data["clarification_questions"]:
                    st.write(f"- {q}")
        with col_p2:
            auto_exec = plan.get("auto_execute", False)
            st.metric("Auto-Execute Status", "✅ Ready" if auto_exec else "❌ Blocked")
            st.write(f"**Requires Clarification:** {'Yes' if plan.get('requires_clarification') else 'No'}")
        
        missed = data.get("reflection", {}).get("missed_items", [])
        if missed:
            st.info(f"🔍 **Self-Reflection (Possible Misses):** {', '.join(missed)}")

    # --- Auto-Execution Button ---
    if plan.get("auto_execute") and not data.get("requires_clarification"):
        st.success("✨ The Agent has high confidence and recommends Auto-Execution.")
        if st.button("⚡ Approve & Execute All Automatically", type="primary", use_container_width=True):
            with st.spinner("Executing all tasks and events..."):
                results = []
                # Execute Jira Tasks
                for task in data.get("jira_packet", []):
                    params = {"summary": task['title'], "description": task['description'], "priority": task['priority'].capitalize(), "issuetype": "Task"}
                    if task.get('due_date'): params["due_date"] = task['due_date']
                    try:
                        res = jira_dispatch("create_issue", params, j_domain, j_email, j_token, j_project)
                        audit_log("EXECUTE_JIRA", "SUCCESS", task['title'])
                        results.append(f"✅ **Jira:** Created '{task['title']}'")
                    except Exception as e:
                        audit_log("EXECUTE_JIRA", "FAILED", f"{task['title']} - {e}")
                        results.append(f"❌ **Jira Error:** Failed to create '{task['title']}' - {str(e)}")
                
                # Execute Calendar Events
                handler = CalendarHandler()
                for event in data.get("calendar_packet", []):
                    if not event.get('datetime'):
                        audit_log("EXECUTE_CALENDAR", "SKIPPED", event['title'])
                        results.append(f"⚠️ **Calendar:** Skipped '{event['title']}' (Missing Date/Time)")
                        continue
                    try:
                        res = handler.execute({"action": "create_event", "title": event['title'], "time": event['datetime']})
                        audit_log("EXECUTE_CALENDAR", "SUCCESS", event['title'])
                        results.append(f"✅ **Calendar:** {res}")
                    except Exception as e:
                        audit_log("EXECUTE_CALENDAR", "FAILED", f"{event['title']} - {e}")
                        results.append(f"❌ **Calendar Error:** Failed to schedule '{event['title']}' - {str(e)}")
                
                st.session_state.execution_results = results
                st.rerun()

    # Show execution results if any
    if st.session_state.get("execution_results"):
        st.divider()
        st.subheader("📊 Execution Results")
        for res in st.session_state.execution_results:
            st.markdown(res)

    st.divider()

    # --- Manual Review & Execution ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🎫 Jira Tasks")
        tasks = data.get("jira_packet", [])
        if not tasks: st.info("No tasks found.")
        for i, task in enumerate(tasks):
            with st.container(border=True):
                st.subheader(task['title'])
                conf = task.get('confidence', 0)
                st.caption(f"Confidence: {conf*100:.0f}% | Priority: {task.get('priority', 'medium').upper()}")
                st.write(task.get('description', ''))
                if task.get('assignee'): st.write(f"👤 Assignee: {task['assignee']}")
                if task.get('due_date'): st.write(f"📅 Due: {task['due_date']}")
                
                if st.button(f"Push Task manually", key=f"jira_man_{i}"):
                    params = {"summary": task['title'], "description": task.get('description', ''), "priority": task.get('priority', 'medium').capitalize(), "issuetype": "Task"}
                    if task.get('due_date'): params["due_date"] = task['due_date']
                    try:
                        res = jira_dispatch("create_issue", params, j_domain, j_email, j_token, j_project)
                        audit_log("MANUAL_JIRA", "SUCCESS", task['title'])
                        st.success("Pushed to Jira!")
                        st.markdown(res)
                    except Exception as e:
                        audit_log("MANUAL_JIRA", "FAILED", f"{task['title']} - {e}")
                        st.error(f"Error: {e}")

    with col2:
        st.header("📅 Calendar Events")
        events = data.get("calendar_packet", [])
        if not events: st.info("No events found.")
        for i, event in enumerate(events):
            with st.container(border=True):
                st.subheader(event['title'])
                conf = event.get('confidence', 0)
                st.caption(f"Confidence: {conf*100:.0f}%")
                st.write(f"⏰ {event.get('datetime') or '⚠️ Time not specified'}")
                parts = event.get('participants', [])
                st.write(f"👥 {', '.join(parts) if parts else 'No participants'}")
                
                if st.button(f"Add Event manually", key=f"cal_man_{i}"):
                    if not event.get('datetime'):
                        st.error("Cannot add event without a valid date/time.")
                    else:
                        try:
                            handler = CalendarHandler()
                            res = handler.execute({"action": "create_event", "title": event['title'], "time": event['datetime']})
                            audit_log("MANUAL_CALENDAR", "SUCCESS", event['title'])
                            st.success(res)
                        except Exception as e:
                            audit_log("MANUAL_CALENDAR", "FAILED", f"{event['title']} - {e}")
                            st.error(f"Error: {e}")

    st.divider()
    if st.button("Reset Session", use_container_width=True):
        del st.session_state.extracted_data
        if "execution_results" in st.session_state:
            del st.session_state.execution_results
        st.rerun()
