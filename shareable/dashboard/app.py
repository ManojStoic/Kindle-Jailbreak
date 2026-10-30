"""Read-only dashboard data service; default deployment binds to loopback."""
from datetime import datetime
from functools import lru_cache
import json
import os
from pathlib import Path
import time
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI
from dashboard.google_data import snapshot

app = FastAPI(title="KindleLab dashboard", docs_url=None, redoc_url=None, openapi_url=None)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "dashboard" / "config.json"

def settings():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

def configured_timezone():
    return ZoneInfo(settings().get("timezone", "UTC"))


@lru_cache(maxsize=1)
def _weather_for_interval(interval: int) -> dict:
    try:
        config = settings()
        if "latitude" not in config or "longitude" not in config:
            return {"status": "not configured"}
        query = urlencode({"latitude": config["latitude"], "longitude": config["longitude"],
                           "current": "temperature_2m,weather_code", "timezone": config.get("timezone", "UTC")})
        request = Request("https://api.open-meteo.com/v1/forecast?" + query, headers={"User-Agent": "KindleLab/1.0"})
        with urlopen(request, timeout=4) as response:
            data = json.load(response)
        current = data["current"]
        return {"status": "available", "temperature_c": current["temperature_2m"],
                "weather_code": current["weather_code"], "observed_at": current["time"]}
    except (URLError, OSError, ValueError, KeyError, TypeError):
        return {"status": "unavailable"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    config = settings()
    now = datetime.now(configured_timezone())
    greeting = os.environ.get("KINDLELAB_GREETING", config.get("greeting", "Hello"))
    google = snapshot()
    return {
        "greeting": greeting,
        "time": now.strftime("%H:%M"), "date": now.strftime("%Y-%m-%d"),
        "timezone": config.get("timezone", "UTC"), "weather_location": config.get("location", "Not configured"),
        "weather": _weather_for_interval(int(time.time() // 900)),
        "calendar": google["calendar"],
        "server": {"status": "not configured"},
        "kindle_wifi": {"status": "not connected to device"},
        "books": {"status": "provided by SimpleUI"},
    }
