import openai
import pinecone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



import dotenv
import datetime
import os.path
import json
import dateutil.parser


SCOPES = ['https://www.googleapis.com/auth/calendar']

class Calendar:

    def __init__(self, token_file_path):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        creds = None
        self.token_file_path = token_file_path
        if os.path.exists('backend/creds/token.json'):
            creds = Credentials.from_authorized_user_file('backend/creds/token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request('backend/creds/credentials.json'))
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'backend/creds/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('backend/creds/token.json', 'w') as token:
                token.write(creds.to_json())

    #Function that returns a list object of the events currently on the calendar
    def get_all_events(self):
        creds = Credentials.from_authorized_user_file(self.token_file_path, SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        # Call the Calendar API to list upcoming events
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        # print('Getting the upcoming 50 events')
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                            maxResults=50, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        return events

    #Function that given an event id will return the event object from the calendar.
    @staticmethod
    def get_event_by_id(self,event_id):
        creds = Credentials.from_authorized_user_file(self.token_file_path, SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        # Call the Calendar API to list upcoming events
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print('Getting the event with id: ' + event_id)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        return event
    
    #Function that given an event id will delete the event from the calendar.
    #If the event is recurring, find its parent event and delete that.

    #Get events within a date range
    def get_events_in_date_range(self,start_date=None,end_date=None):
        creds = Credentials.from_authorized_user_file(self.token_file_path, SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        # Convert the start_date and end_date to UTC format
        time_min = start_date
        time_max = end_date

        # Query the calendar for events within the time range and containing the search term
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        events = events_result.get('items', [])
        return events
    
cal = Calendar('backend/creds/token.json')