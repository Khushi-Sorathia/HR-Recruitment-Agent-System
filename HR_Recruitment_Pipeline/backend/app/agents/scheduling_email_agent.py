from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.core.config import settings
import uuid
import base64
from email.message import EmailMessage
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class ScheduleState(TypedDict):
    candidate_email: str
    availability: str
    meeting_link: str
    email_status: str

def generate_meeting_node(state: ScheduleState):
    # Mocking Google Meet/Zoom integration
    meeting_id = str(uuid.uuid4())[:8]
    state["meeting_link"] = f"https://mock-meet.com/{meeting_id}"
    return state

def dispatch_email_node(state: ScheduleState):
    # Gmail API Authentication logic
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GOOGLE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            else:
                print(f"--- FAILED TO AUTHENTICATE GMAIL API ---")
                print(f"Missing {settings.GOOGLE_CREDENTIALS_FILE}. Cannot dispatch email via Gmail API.")
                state["email_status"] = "Failed: Missing Google Credentials"
                return state

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(f"Congratulations! Please join your technical interview at {state['meeting_link']}")
        message['To'] = state['candidate_email']
        message['From'] = "hr@skysecure.com" # Should match authenticated Gmail sender
        message['Subject'] = 'Skysecure Interview Scheduled'

        # encoded message
        encoded_message = base64.urlsafe_bencode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f"Message Id: {send_message['id']}")
        
        state["email_status"] = "Dispatched via Gmail API successfully"
    except HttpError as error:
        print(f"An error occurred: {error}")
        state["email_status"] = "Failed via Gmail API"

    return state

builder = StateGraph(ScheduleState)
builder.add_node("generate_meeting", generate_meeting_node)
builder.add_node("dispatch_email", dispatch_email_node)
builder.add_edge("generate_meeting", "dispatch_email")
builder.add_edge("dispatch_email", END)
builder.set_entry_point("generate_meeting")

schedule_graph = builder.compile()

def run_scheduling_pipeline(email: str, availability: str) -> dict:
    state = ScheduleState(candidate_email=email, availability=availability, meeting_link="", email_status="")
    return schedule_graph.invoke(state)
