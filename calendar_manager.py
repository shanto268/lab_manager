__author__ = "Sadman Ahmed Shanto"
__email__ = "shanto@usc.edu"

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from dateutil.parser import parse
import os
import pickle
from google.auth.transport.requests import Request

class CalendarManager:
    def __init__(self, email_notifier, client_secret_file="client_secret.json", token_file='token.pickle', scopes=['https://www.googleapis.com/auth/calendar']):
        self.credentials = None
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                self.credentials = pickle.load(token)

        # If there are no valid credentials available, let the user log in.
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes=scopes)
                self.credentials = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(self.credentials, token)

        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.email_notifier = email_notifier

    def create_event(self, title, start_date, end_date, attendees, all_day=False):
        """Create a calendar event without attendees."""
        time_zone = 'America/Los_Angeles'
        if all_day:
            # For all-day events, use 'date' instead of 'dateTime'
            start = {'date': start_date}
            end = {'date': end_date}
        else:
            # For timed events, use 'dateTime'
            start = {'dateTime': start_date, 'timeZone': time_zone}
            end = {'dateTime': end_date, 'timeZone': time_zone}
        # Add attendees if provided
        event_body = {
            'summary': title,
            'start': start,
            'end': end,
            'attendees': [{'email': attendee} for attendee in attendees],
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'email', 'minutes': 24 * 60},
                              {'method': 'popup', 'minutes': 10}],
            },
        }
        print(f"Creating event: {event_body}")
        try:
            event = self.service.events().insert(calendarId='primary', body=event_body).execute()
            print('Event created: %s' % (event.get('htmlLink')))
        except HttpError as e:
            error_message = f"An error occurred in CalendarManager: {e}"
            self.email_notifier.send_email([__email__], "CalendarManager Error", error_message)
            print(error_message)
            raise


    def create_timed_event(self, title, date, start_time_str, attendees, calendar_id='primary'):
        """Create a calendar event based on a start time string."""
        time_zone = 'America/Los_Angeles'
        
        # Parse the start time string and set it to the provided date
        start_time = parse(start_time_str)
        start_datetime = datetime.combine(date.date(), start_time.time())

        # Add one hour to get the end time
        end_datetime = start_datetime + timedelta(hours=1)

        event_body = {
            'summary': title,
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': time_zone},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': time_zone},
            'attendees': [{'email': attendee} for attendee in attendees],
            'reminders': {
                'useDefault': False,
                'overrides': [{'method': 'email', 'minutes': 24 * 60}, {'method': 'popup', 'minutes': 10}],
            },
        }
        print(f"Creating event: {event_body}")
        try:
            event = self.service.events().insert(calendarId=calendar_id, body=event_body).execute()
            print('Event created: %s' % (event.get('htmlLink')))
        except HttpError as e:
            error_message = f"An error occurred in CalendarManager: {e}"
            self.email_notifier.send_email([__email__], "CalendarManager Error", error_message)
            print(error_message)
            raise
