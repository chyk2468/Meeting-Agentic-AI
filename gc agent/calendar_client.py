import datetime
import dateparser
from pytz import timezone
from auth import get_calendar_service

# Default timezone for the assistant
DEFAULT_TZ = 'Asia/Kolkata'

class CalendarClient:
    def __init__(self):
        self.service = get_calendar_service()
        if not self.service:
            raise Exception("Failed to initialize Google Calendar Service.")

    def create_event(self, title, time_text, duration_minutes=60):
        """
        Creates an event on the user's primary calendar.
        :param title: Summary of the event
        :param time_text: Natural language time (e.g., "tomorrow at 5pm")
        :param duration_minutes: Duration in minutes
        """
        # Parse time using dateparser
        tz = timezone(DEFAULT_TZ)
        start_time = dateparser.parse(
            time_text, 
            settings={'RELATIVE_BASE': datetime.datetime.now(), 'TIMEZONE': DEFAULT_TZ, 'RETURN_AS_TIMEZONE_AWARE': True}
        )

        if not start_time:
            return {"error": f"Could not parse time: {time_text}"}

        # Calculate end time
        end_time = start_time + datetime.timedelta(minutes=duration_minutes)

        event = {
            'summary': title,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': DEFAULT_TZ,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': DEFAULT_TZ,
            },
        }

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return {
                "status": "success",
                "message": f"Event created: {event.get('htmlLink')}",
                "event_id": event.get('id'),
                "title": title,
                "start": start_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            }
        except Exception as e:
            return {"error": str(e)}

    def list_events(self, max_results=10, time_min=None, time_max=None):
        """
        Lists upcoming events, optionally within a time range.
        :param max_results: Maximum events to return
        :param time_min: RFC3339 timestamp or natural language (e.g., "today")
        :param time_max: RFC3339 timestamp or natural language
        """
        tz = timezone(DEFAULT_TZ)
        now = datetime.datetime.now(tz)

        # Parse time_min
        if time_min:
            parsed_min = dateparser.parse(time_min, settings={'RELATIVE_BASE': now, 'TIMEZONE': DEFAULT_TZ, 'RETURN_AS_TIMEZONE_AWARE': True})
            t_min = parsed_min.isoformat() if parsed_min else now.isoformat()
        else:
            t_min = now.isoformat()

        # Parse time_max
        t_max = None
        if time_max:
            parsed_max = dateparser.parse(time_max, settings={'RELATIVE_BASE': now, 'TIMEZONE': DEFAULT_TZ, 'RETURN_AS_TIMEZONE_AWARE': True})
            t_max = parsed_max.isoformat() if parsed_max else None

        try:
            events_result = self.service.events().list(
                calendarId='primary', 
                timeMin=t_min,
                timeMax=t_max,
                maxResults=max_results, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                return {"message": "No upcoming events found.", "events": []}

            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    "id": event['id'],
                    "title": event.get('summary', '(No title)'),
                    "start": start
                })
            
            return {"status": "success", "events": formatted_events}
        except Exception as e:
            return {"error": str(e)}

    def delete_event(self, event_id):
        """
        Deletes an event by its ID.
        """
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return {"status": "success", "message": f"Successfully deleted event with ID: {event_id}"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Small local test
    client = CalendarClient()
    # print(client.list_events())
