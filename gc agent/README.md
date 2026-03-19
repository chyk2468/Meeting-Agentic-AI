# 📅 Google Calendar AI Assistant

An AI-powered scheduling assistant that helps you manage your Google Calendar using natural language. Built with Streamlit and powered by Groq's Llama 3.3 70B model.

## 🚀 Features

- **Natural Language Commands**: Just type what you want to do (e.g., "Schedule a meeting with HR tomorrow at 2 PM").
- **Event Management**:
    - **List Events**: View your upcoming schedule.
    - **Create Events**: Add new events with a confirmation step to ensure accuracy.
    - **Delete Events**: Remove events by title or keywords.
- **Batch Processing**: Create multiple events in a single request.
- **Intelligent Context**: Remembers recent events to handle follow-up commands like "Delete that meeting".
- **Modern UI**: Clean and responsive interface built with Streamlit.

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **LLM Engine**: [Groq Cloud](https://groq.com/) (Llama-3.3-70b-versatile)
- **API**: [Google Calendar API](https://developers.google.com/calendar)
- **Language**: Python 3.x

## 📋 Prerequisites

Before running the application, you'll need:

1.  **Groq API Key**: Get it from the [Groq Console](https://console.groq.com/).
2.  **Google Cloud Project**:
    -   Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
    -   Enable the **Google Calendar API**.
    -   Configure the **OAuth Consent Screen** (Internal/External).
    -   Create **OAuth 2.0 Client IDs** (Desktop App).
    -   Download the JSON file and rename it to `credentials.json`.

## ⚙️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**:
    Create a `.env` file in the root directory and add your Groq API key:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    ```

4.  **Add Google Credentials**:
    Place your `credentials.json` file in the root directory.

## 🏃 Usage

1.  **Start the application**:
    ```bash
    streamlit run app.py
    ```

2.  **Authenticate**:
    On the first run, a browser window will open asking you to log in to your Google account and grant permissions. A `token.json` file will be created to store your session.

3.  **Interact with the AI**:
    -   "What do I have planned for today?"
    -   "Schedule a coffee chat with Sarah on Friday at 10 AM and a gym session at 6 PM."
    -   "Delete the gym session."

## 📂 Project Structure

- `app.py`: The main Streamlit application and UI logic.
- `agent.py`: AI agent logic using Groq to parse natural language into structured actions.
- `actions.py`: Handles the execution of actions (create, list, delete) against the Google Calendar.
- `calendar_client.py`: Wrapper for the Google Calendar API service.
- `auth.py`: Manages OAuth2 authentication and token refreshing.
- `requirements.txt`: List of required Python packages.

## 📝 License

This project is open-source. Feel free to contribute!
