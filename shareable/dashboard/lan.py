"""Authenticated, TLS-only snapshot endpoint for the local Kindle."""
from pathlib import Path
import secrets

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse

from dashboard.app import dashboard
from dashboard.export_snapshot import snapshot_lines

LAN_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "dashboard" / "lan"
TOKEN_FILE = LAN_DIR / "token.txt"
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/snapshot", response_class=PlainTextResponse)
def snapshot(authorization: str = Header(default="")) -> PlainTextResponse:
    try:
        token = TOKEN_FILE.read_text(encoding="ascii").strip()
    except OSError:
        raise HTTPException(status_code=503, detail="Not configured") from None
    if not token or not secrets.compare_digest(authorization, "Bearer " + token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return PlainTextResponse("\n".join(snapshot_lines(dashboard())) + "\n",
                             headers={"Cache-Control": "no-store"})
