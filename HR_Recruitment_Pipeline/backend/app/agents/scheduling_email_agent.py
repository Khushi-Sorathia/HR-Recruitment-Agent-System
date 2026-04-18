from typing import TypedDict
from langgraph.graph import StateGraph, END
from app.core.config import settings
import uuid
import base64
import smtplib
import os
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class ScheduleState(TypedDict):
    candidate_email: str
    candidate_name: str
    job_role: str
    availability: str
    meeting_link: str
    email_status: str


def generate_meeting_node(state: ScheduleState):
    """Generate a unique meeting link."""
    meeting_id = str(uuid.uuid4())[:8]
    meeting_link = f"https://meet.google.com/mock-{meeting_id}"
    return {"meeting_link": meeting_link}


def dispatch_email_node(state: ScheduleState):
    """Send confirmation emails via Gmail API or SMTP fallback."""

    # Build the email content
    subject = f"Interview Scheduled — {state['job_role']} Position"
    body = f"""Dear {state['candidate_name']},

Congratulations on progressing in the recruitment pipeline for the {state['job_role']} position!

Your interview has been scheduled based on your indicated availability: {state['availability']}

Please join via the following link:
{state['meeting_link']}

Please be on time and have a stable internet connection ready.

Best regards,
HR Recruitment Team"""

    # Try Gmail API first, then fall back to SMTP
    email_sent = False

    # ---------- Gmail API Attempt ----------
    if os.path.exists(settings.GOOGLE_CREDENTIALS_FILE) or os.path.exists("token.json"):
        try:
            creds = None
            if os.path.exists("token.json"):
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.GOOGLE_CREDENTIALS_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    with open("token.json", "w") as token:
                        token.write(creds.to_json())

            if creds and creds.valid:
                service = build("gmail", "v1", credentials=creds)

                # Send to candidate
                message = EmailMessage()
                message.set_content(body)
                message["To"] = state["candidate_email"]
                message["Subject"] = subject
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                service.users().messages().send(
                    userId="me", body={"raw": encoded_message}
                ).execute()

                # Send to HR team
                if settings.HR_TEAM_EMAIL:
                    hr_message = EmailMessage()
                    hr_message.set_content(
                        f"Interview scheduled for {state['candidate_name']} ({state['candidate_email']}) "
                        f"for {state['job_role']}.\n\n"
                        f"Availability: {state['availability']}\n"
                        f"Meeting Link: {state['meeting_link']}"
                    )
                    hr_message["To"] = settings.HR_TEAM_EMAIL
                    hr_message["Subject"] = f"[HR] Interview Scheduled — {state['candidate_name']}"
                    encoded_hr = base64.urlsafe_b64encode(hr_message.as_bytes()).decode()
                    service.users().messages().send(
                        userId="me", body={"raw": encoded_hr}
                    ).execute()

                email_sent = True
                return {"email_status": "Dispatched via Gmail API successfully"}
        except (HttpError, Exception) as e:
            print(f"Gmail API failed: {e}. Falling back to SMTP.")

    # ---------- SMTP Fallback ----------
    if not email_sent and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USER
            msg["To"] = state["candidate_email"]

            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

                # Also send to HR
                if settings.HR_TEAM_EMAIL:
                    hr_msg = EmailMessage()
                    hr_msg.set_content(
                        f"Interview scheduled for {state['candidate_name']} ({state['candidate_email']}) "
                        f"for {state['job_role']}.\n"
                        f"Meeting Link: {state['meeting_link']}"
                    )
                    hr_msg["Subject"] = f"[HR] Interview Scheduled — {state['candidate_name']}"
                    hr_msg["From"] = settings.SMTP_USER
                    hr_msg["To"] = settings.HR_TEAM_EMAIL
                    server.send_message(hr_msg)

            email_sent = True
            return {"email_status": "Dispatched via SMTP successfully"}
        except Exception as e:
            print(f"SMTP failed: {e}")

    if not email_sent:
        return {
            "email_status": f"Email not sent — no Gmail credentials or SMTP config found. "
            f"Meeting link generated: {state['meeting_link']}"
        }

    return state


builder = StateGraph(ScheduleState)
builder.add_node("generate_meeting", generate_meeting_node)
builder.add_node("dispatch_email", dispatch_email_node)
builder.add_edge("generate_meeting", "dispatch_email")
builder.add_edge("dispatch_email", END)
builder.set_entry_point("generate_meeting")

schedule_graph = builder.compile()


def run_scheduling_pipeline(
    email: str,
    candidate_name: str,
    job_role: str,
    availability: str,
) -> dict:
    state = ScheduleState(
        candidate_email=email,
        candidate_name=candidate_name,
        job_role=job_role,
        availability=availability,
        meeting_link="",
        email_status="",
    )
    return schedule_graph.invoke(state)
