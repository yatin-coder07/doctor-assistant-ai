import os
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build



SCOPES = ['https://www.googleapis.com/auth/calendar']

# 🔥 Absolute paths (FIXES your error)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")



def get_service():
    creds = None

    print("📂 Looking for credentials at:", CREDENTIALS_PATH)

    # Load token if exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid creds → login
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH,
            SCOPES
        )

       
        creds = flow.run_local_server(port=8080)

      
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)



def create_event(date: str, slot: str):
    try:
        service = get_service()

       
        start_time = datetime.strptime(f"{date} {slot}", "%Y-%m-%d %H:%M")
        end_time = start_time + timedelta(minutes=30)

        event = {
            "summary": "Doctor Appointment - Dr Ahuja",
            "description": "Booked via AI Assistant",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
        }

        event = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        print("✅ Event created:", event.get("htmlLink"))

    except Exception as e:
      
        print("❌ Google Calendar Error:", e)