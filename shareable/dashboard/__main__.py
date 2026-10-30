"""Launch the development service on this computer only."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("dashboard.app:app", host="127.0.0.1", port=8765, access_log=False)
