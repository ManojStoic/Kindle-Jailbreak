"""Read-only Google Calendar integration for the local service."""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
import time

PRIVATE_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "dashboard" / "google"
CLIENT_FILE = PRIVATE_DIR / "credentials.json"
TOKEN_FILE = PRIVATE_DIR / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.readonly",
]


def authorize() -> None:
    """Run only on explicit user action; opens Google's consent flow."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not CLIENT_FILE.is_file():
        raise FileNotFoundError("Google Desktop OAuth credentials are not configured")
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    credentials = flow.run_local_server(host="127.0.0.1", port=0,
                                        authorization_prompt_message=None)
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")


def _credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN_FILE.is_file():
        return None
    credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return credentials if credentials.valid else None


@lru_cache(maxsize=1)
def _snapshot_for_interval(_interval: int) -> dict:
    result = {"calendar": {"status": "not connected", "events": []}}
    if not TOKEN_FILE.is_file():
        return result
    try:
        from googleapiclient.discovery import build

        credentials = _credentials()
        if not credentials:
            return result
        now = datetime.now(timezone.utc)
        calendar = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        events = calendar.events().list(
            calendarId="primary", timeMin=now.isoformat(),
            timeMax=(now + timedelta(days=7)).isoformat(),
            maxResults=3, singleEvents=True, orderBy="startTime",
            fields="items(summary,start)",
        ).execute().get("items", [])
        result["calendar"] = {"status": "connected", "events": [
            {"title": e.get("summary", "(Untitled)"),
             "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date"))}
            for e in events]}
    except Exception:
        # Avoid logging URLs, tokens, account identifiers or event/task contents.
        if result["calendar"]["status"] != "connected":
            result["calendar"]["status"] = "unavailable"
    return result


def snapshot() -> dict:
    return _snapshot_for_interval(int(time.time() // 300))


if __name__ == "__main__":
    authorize()
    print("Google authorization saved locally.")
