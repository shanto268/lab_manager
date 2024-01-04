from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class CalendarManager:
    def __init__(self, service_key, email_notifier):
        self.credentials = Credentials.from_service_account_info(service_key)
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.email_notifier = email_notifier

    def create_event(self, title, start_date, end_date, attendees):
        """Create a calendar event."""
        event = {
            'summary': title,
            'start': {'date': start_date},
            'end': {'date': end_date},
            'attendees': [{'email': attendee} for attendee in attendees],
        }

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
        except HttpError as e:
            error_message = f"An error occurred in CalendarManager: {e}"
            self.email_notifier.send_email(["shanto@usc.edu"], "CalendarManager Error", error_message)
            print(error_message)
            raise

