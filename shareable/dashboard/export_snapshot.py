"""Create a compact, private offline snapshot for the Kindle dashboard."""
from datetime import datetime
from pathlib import Path
import unicodedata

from dashboard.app import configured_timezone, dashboard

OUTPUT = Path(__file__).resolve().parent.parent / "artifacts" / "dashboard" / "kindle-snapshot.txt"


def clean(value, limit=30):
    text = "".join(" " if unicodedata.category(ch).startswith("C") else ch for ch in str(value or "")).split()
    text = " ".join(text)
    return text if len(text) <= limit else text[:limit - 1] + "…"


def snapshot_lines(data):
    weather = data.get("weather", {})
    weather_text = f"{weather['temperature_c']:g} C" if weather.get("status") == "available" else "unavailable"
    events = data.get("calendar", {}).get("events", [])
    event = "No upcoming events" if data.get("calendar", {}).get("status") == "connected" else "Not connected"
    if events:
        first = events[0]
        raw_start = first.get("start") or ""
        try:
            if len(raw_start) == 10:
                event_date = datetime.fromisoformat(raw_start).strftime("%d %b")
            else:
                event_date = datetime.fromisoformat(raw_start.replace("Z", "+00:00")).astimezone(configured_timezone()).strftime("%d %b")
        except (ValueError, TypeError):
            event_date = "Date unavailable"
        event = f"{event_date}  {clean(first.get('title'), 25)}"
    updated = datetime.now(configured_timezone()).strftime("%d %b %H:%M")
    return [f"Weather: {weather_text}", f"Event: {event}", f"Updated: {updated}"]


def main():
    lines = snapshot_lines(dashboard())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    print("Private dashboard snapshot created; contents withheld.")


if __name__ == "__main__":
    main()
