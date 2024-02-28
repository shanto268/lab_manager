import os
import pickle
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def authenticate_google_calendar():
    """Authenticate and return a Google Calendar API service."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def create_event(service, event):
    """Create an event on the user's calendar."""
    event = service.events().insert(calendarId=MM_calendar_ID, body=event).execute()
    print(f"Event created: {event.get('htmlLink')}")

def create_calendar_events(pres_list):
    service = authenticate_google_calendar()

    for pres in pres_list:
        # Check if minutes part is missing and add it if necessary
        time_begin = pres['time_begin'] if ':' in pres['time_begin'] else pres['time_begin'][:-2] + ':00' + pres['time_begin'][-2:]
        time_end = pres['time_end'] if ':' in pres['time_end'] else pres['time_end'][:-2] + ':00' + pres['time_end'][-2:]

        start_time = datetime.strptime(f"{pres['pres_date']} {time_begin}", "%m/%d/%Y %I:%M%p")
        end_time = datetime.strptime(f"{pres['pres_date']} {time_end}", "%m/%d/%Y %I:%M%p")
        event_body = {
            'summary': pres['title'],
            'location': pres['location'],
            'description': f"Presented by: {pres['name']}\n\nAbstract: {pres['abstract']}",
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': MM_TIMEZONE,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': MM_TIMEZONE,
            },
        }
        create_event(service, event_body)


def create_pres_list_from_aps(url):
    pres_list = []

    # Send a GET request to the URL
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.find('meta', attrs={'name': 'citation_title'})['content']
    authors_meta = soup.find('meta', attrs={'name': 'citation_authors'})['content']
    authors = authors_meta.split(';')
    presenter = authors[0] if authors else ""
    abstract_div = soup.find('div', class_='largernormal')
    abstract_text = abstract_div.text if abstract_div else ""
    location_text = soup.find(string=lambda x: x and "Room:" in x)
    location = location_text.split("Room:")[1].strip() if location_text else "Not specified"
    pres_date_meta = soup.find('meta', attrs={'name': 'citation_date'})['content']
    pres_date = pres_date_meta

    session_title_tag = soup.find('h3')
    if session_title_tag and "Poster Session" in session_title_tag.text:
        # Extract times from parenthesis in session title
        time_text = re.search(r'\((\d+pm)-(\d+pm) CST\)', session_title_tag.text)
        time_begin, time_end = time_text.groups() if time_text else ("Not specified", "Not specified")
    else:
        # Extract the times from the content following the citation_date
        time_info = soup.find('p', style="margin-top: 0px;").find_next_sibling('p')
        if time_info:
            time_text = time_info.text.strip()
            times = time_text.split('–')
            # Example adjustments within your existing code
            time_begin = times[0].strip().replace('\xa0', '').lower() if len(times) > 0 else "Not specified"
            time_end = times[1].strip().replace('\xa0', '').lower() if len(times) > 1 else "Not specified"
        else:
            time_begin, time_end = "Not specified", "Not specified"

    pres_list.append({
        "name": presenter.strip(),
        "title": title.strip(),
        "pres_date": pres_date,
        "time_begin": time_begin,
        "time_end": time_end,
        "abstract": abstract_text.strip(),
        "location": location
    })

    return pres_list

def process_aps_urls(url_list):
    """
    Process a list of APS URLs to extract presentation details.

    Parameters:
    - url_list: A list of strings, where each string is a URL to an APS abstract page.

    Returns:
    - A list of dictionaries, where each dictionary contains details of a presentation.
    """
    all_pres_details = []

    for url in url_list:
        pres_details = create_pres_list_from_aps(url)
        # Assuming each URL corresponds to a single presentation,
        # and create_pres_list_from_aps returns a list with a single dict,
        # we extend the master list.
        all_pres_details.extend(pres_details)
    
    return all_pres_details

if __name__ == "__main__":
    # read calendar ID from .env
    load_dotenv()
    MM_calendar_ID = os.getenv("MM_calendar_ID")
    MM_TIMEZONE = 'America/Chicago'  # Minneapolis time
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    url_list = [
        "https://meetings.aps.org/Meeting/MAR24/Session/J00.249",
        "https://meetings.aps.org/Meeting/MAR24/Session/B54.6",
        "https://meetings.aps.org/Meeting/MAR24/Session/J00.246",
        "https://meetings.aps.org/Meeting/MAR24/Session/J00.265",
        "https://meetings.aps.org/Meeting/MAR24/Session/K50.11",
        "https://meetings.aps.org/Meeting/MAR24/Session/S50.2",
        "https://meetings.aps.org/Meeting/MAR24/Session/A47.8",
        "https://meetings.aps.org/Meeting/MAR24/Session/K50.5",
        "https://meetings.aps.org/Meeting/MAR24/Session/M48.12",
        "https://meetings.aps.org/Meeting/MAR24/Session/S50.1",
    ]
    all_pres_details = process_aps_urls(url_list)
    create_calendar_events(all_pres_details)