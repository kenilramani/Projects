import os
import datetime
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'
TIMEZONE_STR = 'Asia/Kolkata'
TZ_INFO = ZoneInfo(TIMEZONE_STR)

SERVICE_ACCOUNT_FILE = "service_account.json"


def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    return build('calendar', 'v3', credentials=credentials)


def check_availability(service, start_dt, end_dt):
    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": TIMEZONE_STR,
        "items": [{"id": CALENDAR_ID}],
    }

    events_result = service.freebusy().query(body=body).execute()
    busy_times = events_result["calendars"][CALENDAR_ID]["busy"]

    return len(busy_times) == 0


def book_demo_slot(name: str, email: str, date: str, time: str):
    try:
        service = get_calendar_service()

        start_dt = datetime.datetime.fromisoformat(f"{date}T{time}")
        start_dt = start_dt.replace(tzinfo=TZ_INFO)
        end_dt = start_dt + datetime.timedelta(hours=1)

        if not check_availability(service, start_dt, end_dt):
            return {
                "status": "busy",
                "message": "That time slot is already booked. Please choose another time."
            }

        event = {
            'summary': f'Demo with {name}',
            'description': f'Booked via VoiceBot.\nClient: {name}\nEmail: {email}',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': TIMEZONE_STR,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': TIMEZONE_STR,
            },
            'attendees': [{'email': email}],
        }

        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        formatted_date = start_dt.strftime('%A, %d %B')
        formatted_time = start_dt.strftime('%I:%M %p')

        return {
            "status": "success",
            "message": f"Your demo is confirmed for {formatted_date} at {formatted_time}. A calendar invite has been sent to {email}."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Calendar booking failed: {str(e)}"
        }
