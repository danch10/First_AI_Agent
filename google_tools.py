import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_google_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_calendar_events(days_ahead=1):
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=days_ahead)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now.isoformat() + 'Z',
        timeMax=end.isoformat() + 'Z',
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if not events:
        return f"No events in the next {days_ahead} day(s)."
    lines = []
    for e in events:
        start = e['start'].get('dateTime', e['start'].get('date'))
        lines.append(f"- {e['summary']} at {start}")
    return "\n".join(lines)

def create_calendar_event(title, date, time, duration_hours=1):
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    start = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    end = start + datetime.timedelta(hours=duration_hours)
    event = {
        'summary': title,
        'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Jerusalem'},
        'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Jerusalem'},
    }
    service.events().insert(calendarId='primary', body=event).execute()
    return f"Created event: '{title}' on {date} at {time}"

def get_emails(max_results=5):
    creds = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'UNREAD'],
        maxResults=max_results
    ).execute()
    messages = results.get('messages', [])
    if not messages:
        return "No unread emails."
    lines = []
    for msg in messages:
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'Subject']
        ).execute()
        headers = {h['name']: h['value'] for h in detail['payload']['headers']}
        lines.append(f"- From: {headers.get('From', '?')} | Subject: {headers.get('Subject', '?')}")
    return "\n".join(lines)

def send_email(to, subject, body):
    import base64
    from email.mime.text import MIMEText
    creds = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId='me', body={'raw': raw}
    ).execute()
    return f"Email sent to {to} with subject '{subject}'"