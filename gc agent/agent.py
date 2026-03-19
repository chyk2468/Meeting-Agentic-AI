import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CalendarAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise Exception("GROQ_API_KEY not found in .env file.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
        
        self.system_prompt = """
        You are a Google Calendar AI Assistant. Your job is to convert natural language input into structured JSON actions for the calendar.

        Supported Actions:
        1. create_event: Creates an event. Requires 'title' and 'time'.
        2. list_events: Lists upcoming events. Can optionally take 'time_min' and 'time_max' to filter by date/time (e.g. for a specific day).
        3. delete_event: Deletes an event. Requires 'event_id' OR 'query' (if title is provided).

        Rules:
        - Output ONLY valid JSON with a single key 'actions' which is a LIST of objects.
        - No explanation text.
        - If multiple events are mentioned, include them all in the 'actions' list.
        - For 'list_events' on a specific day (e.g., "events for March 26"), set 'time_min' to the start of the day and 'time_max' to the end of that day.
        - If the user asks to delete an event by title (e.g., "delete the HR meeting"), put the title in the 'query' field.
        - If the user provides a specific ID, use 'event_id'.
        - If the user says "delete my last event" and you don't have an ID, set 'query' to "last".
        - If input is unclear, return an error action in the list.

        Example JSON Format:
        {
          "actions": [
            {"action": "create_event", "title": "Meeting A", "time": "tomorrow 10am"},
            {"action": "create_event", "title": "Meeting B", "time": "tomorrow 2pm"}
          ]
        }
        """

    def get_action(self, user_input, conversation_history=""):
        """
        Processes user input and returns a structured JSON action.
        """
        try:
            prompt = f"History: {conversation_history}\nUser: {user_input}"
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            return json.loads(response_text)
        except Exception as e:
            return {"action": "error", "message": str(e)}

if __name__ == "__main__":
    # Test agent
    agent = CalendarAgent()
    # print(agent.get_action("Schedule a meeting with Kanna tomorrow at 5pm"))
