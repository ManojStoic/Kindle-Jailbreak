"""Serve the protected dashboard only on the selected private address."""
import json
import uvicorn

from dashboard.lan import LAN_DIR


def main():
    config = json.loads((LAN_DIR / "config.json").read_text(encoding="utf-8"))
    uvicorn.run("dashboard.lan:app", host=config["host"], port=config["port"],
                ssl_certfile=str(LAN_DIR / "server-cert.pem"),
                ssl_keyfile=str(LAN_DIR / "server-key.pem"), access_log=False)


if __name__ == "__main__":
    main()
