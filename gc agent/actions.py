from calendar_client import CalendarClient

class ActionHandler:
    def __init__(self):
        self.client = CalendarClient()
        self.last_fetched_events = []

    def execute(self, action_json):
        """
        Executes an action based on the AI's JSON output.
        """
        action = action_json.get("action")
        
        if action == "create_event":
            title = action_json.get("title")
            time = action_json.get("time")
            if not title or not time:
                return "Error: Missing title or time for creating an event."
            
            result = self.client.create_event(title, time)
            if "error" in result:
                return f"Failed to create event: {result['error']}"
            return f"✅ Event created! \"{result['title']}\" at {result['start']}."

        elif action == "list_events":
            time_min = action_json.get("time_min")
            time_max = action_json.get("time_max")
            
            result = self.client.list_events(time_min=time_min, time_max=time_max)
            if "error" in result:
                return f"Failed to list events: {result['error']}"
            
            events = result.get("events", [])
            if not events:
                return "You have no upcoming events."
            
            self.last_fetched_events = events # Store for context (e.g. deletion)
            
            output = "📅 **Upcoming Events:**\n"
            for i, event in enumerate(events, 1):
                output += f"{i}. {event['title']} ({event['start']})\n"
            return output

        elif action == "delete_event":
            event_id = action_json.get("event_id")
            query = action_json.get("query", "").lower()
            
            # If no ID provided, try to resolve from query or history
            if not event_id or event_id == "event_id_here":
                # Check history first (last fetched events)
                if self.last_fetched_events:
                    found_event = None
                    if query == "last":
                        found_event = self.last_fetched_events[0]
                    else:
                        # Try to match query with titles in history
                        for event in self.last_fetched_events:
                            if query in event["title"].lower():
                                found_event = event
                                break
                    
                    if found_event:
                        event_id = found_event["id"]
                        title = found_event["title"]
                    else:
                        # If not in history, search specifically for this query
                        list_result = self.client.list_events(max_results=5)
                        events = list_result.get("events", [])
                        for event in events:
                            if query in event["title"].lower():
                                event_id = event["id"]
                                title = event["title"]
                                break
                else:
                    # No history, list and search
                    list_result = self.client.list_events(max_results=5)
                    events = list_result.get("events", [])
                    for event in events:
                        if query == "last" or (query and query in event["title"].lower()):
                            event_id = event["id"]
                            title = event["title"]
                            break
            else:
                title = "specified"

            if not event_id or event_id == "event_id_here":
                return f"Error: Could not find an event matching '{query or 'your request'}'. Please list them first."

            result = self.client.delete_event(event_id)
            if "error" in result:
                return f"Failed to delete event: {result['error']}"
            return f"🗑️ Successfully deleted event: {title}."

        elif action == "error":
            return f"❌ AI Error: {action_json.get('message', 'Unknown error')}"

        else:
            return "Sorry, I'm not sure how to handle that action yet."

if __name__ == "__main__":
    # Test handler
    handler = ActionHandler()
    # print(handler.execute({"action": "list_events"}))
