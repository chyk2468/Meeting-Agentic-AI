# 🧠 Master Agentic AI: Unified Jira & Google Calendar Orchestrator

An advanced "Agent-of-Agents" system that uses **Groq (Llama 3.3 70B)** to autonomously analyze meeting transcripts, notes, and conversations. It intelligently extracts actionable tasks for **Jira** and time-based events for **Google Calendar**, providing a unified command center for your entire workflow.

---

## 🚀 Key Features

- **Master Orchestration:** A single "brain" that coordinates between specialized sub-agents.
- **Autonomous Planning:** The agent analyzes input and generates an internal execution plan before taking action.
- **Confidence Scoring:** Every extracted item includes a confidence score (0-100%) to ensure reliability.
- **Self-Reflection Pass:** The AI performs a second pass over your input to catch any missed details or implied tasks.
- **Auto-Execution Mode:** If confidence is high, the agent unlocks a "One-Click Approve All" feature to batch-process all tasks and events.
- **Clarification Queue:** If the input is ambiguous, the agent generates specific questions instead of guessing.
- **Streamlit Unified UI:** A polished, dark-themed dashboard for real-time monitoring and manual overrides.

---

## 📂 Project Structure

```text
agentic-ai/
├── unified_app.py          # The Master Agentic AI (Main Entry Point)
├── gc agent/               # Google Calendar Specialist Agent
│   ├── app.py              # Sub-agent UI
│   ├── auth.py             # OAuth2 Authentication logic
│   ├── actions.py          # Calendar action handlers
│   └── calendar_client.py  # Google Calendar API wrapper
└── Jira AI Agent/          # Jira Management Specialist Agent
    ├── app.py              # Sub-agent UI
    ├── agent.py            # Jira-specific intent parsing
    ├── actions.py          # Jira action dispatchers
    ├── jira_client.py      # Jira REST API wrapper
    └── vector_store.py     # ChromaDB RAG (for project context)
```

---

## 🛠️ Tech Stack

- **LLM Engine:** Groq Cloud (Llama-3.3-70b-versatile)
- **Frontend:** Streamlit (Custom CSS & Interactive Components)
- **APIs:** Jira REST API v3, Google Calendar API v3
- **Database:** ChromaDB (Vector Store for Jira context)
- **Language:** Python 3.10+

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd agentic-ai
```

### 2. Install Dependencies
Ensure you have all required packages installed for the master app and both sub-agents:
```bash
pip install streamlit groq python-dotenv google-auth google-auth-oauthlib google-api-python-client dateparser pytz jira requests chromadb
```

### 3. Configuration
The Master Agent pulls credentials from the sub-agent directories. Ensure you have the following files in place:

#### **Google Calendar (`gc agent/`):**
1.  **`.env`**: Add your `GROQ_API_KEY`.
2.  **`credentials.json`**: Download your OAuth 2.0 Client ID (Desktop) from the [Google Cloud Console](https://console.cloud.google.com/).

#### **Jira Agent (`Jira AI Agent/`):**
1.  **`.env`**: Add your `GROQ_API_KEY`, `JIRA_EMAIL`, `JIRA_API_KEY` (Token), and `JIRA_DOMAIN`.

---

## 🏃 Usage

### Start the Master Agent
Run the following command from the **root directory**:
```bash
streamlit run unified_app.py
```

### The Workflow
1.  **Input:** Paste a meeting transcript or raw notes into the text area.
2.  **Analyze:** The Agent will parse the text, assign confidence scores, and perform a self-reflection pass.
3.  **Review:** Examine the "Agent's Internal Plan." If it has questions, they will appear in a warning box.
4.  **Execute:** 
    *   Click **"⚡ Approve & Execute All Automatically"** for a high-confidence batch upload.
    *   Use the **"Push Task"** or **"Add Event"** buttons on individual cards for manual control.

---

## 🔒 Security & Reliability

- **Absolute Path Resolution:** The system uses robust path handling to ensure `credentials.json` and `token.json` are always correctly located.
- **Module Isolation:** Specialized module loading prevents name collisions between the Jira and Calendar `actions.py` files.
- **Error Handling:** Real-time API logs provide immediate feedback on every execution attempt.

---

<p align="center">
  Built with ❤️ for autonomous productivity.
</p>
