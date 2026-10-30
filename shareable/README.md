# KindleLab: personal reading dashboard

An experimental, local-first SimpleUI dashboard for KOReader: a greeting, the
Kindle's local clock and Wi-Fi name, plus a weather and Google Calendar snapshot
from a computer on the same network. SimpleUI provides the book library, reading
statistics and layout. Google Calendar and weather are optional. No Google Tasks,
game, books, wallpaper, personal settings or credentials are included.

The original KindleLab dashboard was tested and worked on a Paperwhite 3. This
shareable version adapts that setup for other users; its changes have not yet been
tested on a Kindle. SimpleUI and KOReader APIs and layouts may change. It is not
a universal installer: newer Kindles may use MTP rather than a
drive letter, and compatibility varies by exact model and firmware.

## Before installing

1. Identify the model and firmware on the device; keep serial numbers private.
2. Back up accessible USB files and verify the backup. This does not back up the
   firmware or partitions. Understand the recovery limitations for your device.
3. Consult the current [KindleModding jailbreak guide and wizard](https://kindlemodding.org/jailbreaking/).
   Do not assume that a compatible jailbreak or recovery method exists. Follow
   the exact current procedure only after its risks are understood; firmware
   updates can remove or prevent jailbreak access.
4. After jailbreaking, use [KindleModding's KOReader guide](https://kindlemodding.org/jailbreaking/whats-next/getting-koreader/)
   and [KOReader's Kindle installation guide](https://github.com/koreader/koreader/wiki/Installation-on-Kindle-devices).
   Verify the package and dependencies for the device. Keep the original Kindle reader.
5. Install [SimpleUI](https://github.com/doctorhetfield-cmd/simpleui.koplugin)
   from its release instructions. Its upstream page currently requires KOReader
   2026.03 or newer and the CoverBrowser plugin. Follow upstream for version-specific details.

## Dashboard setup on Windows

Run these PowerShell commands from this `shareable` directory. They create a
local virtual environment, install Python dependencies, and copy an example
configuration into the ignored `artifacts` directory:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force artifacts\dashboard
Copy-Item config.example.json artifacts\dashboard\config.json
```

Edit `artifacts/dashboard/config.json`: set your preferred greeting, IANA time
zone, location name and approximate latitude/longitude. Do not use precise home
coordinates: weather requests send coordinates to [Open-Meteo](https://open-meteo.com/).
The Kindle's clock uses its own local time zone; set that separately on the device.
The laptop's configured time zone controls event dates and snapshot timestamps.

For calendar access, follow [Google's Python Calendar quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python):
enable the Calendar API, configure consent and a Desktop OAuth client, and if the
app is in testing add your account as a test user. Put your downloaded credentials
at `artifacts/dashboard/google/credentials.json`, then run:

```powershell
.\.venv\Scripts\python.exe -m dashboard.google_data
```

Review the read-only calendar permission in the browser. Tokens remain in the
ignored artifacts directory. Testing-mode refresh tokens can expire; repeat
authorization if needed. Calendar content will be shown on the device.

To make a snapshot without Wi-Fi sync:

```powershell
.\.venv\Scripts\python.exe -m dashboard.export_snapshot
```

Copy `artifacts/dashboard/kindle-snapshot.txt` to
`kindlelab/dashboard-snapshot.txt` on the Kindle's user storage. This is a fixed
snapshot until refreshed. Keep it private: it can contain event titles.

## Installing the dashboard plugin

Exit KOReader before connecting USB. Where the device presents a writable storage
volume, copy the `kindlelab-dashboard.koplugin` folder into `koreader/plugins/`.
Create `kindlelab/dashboard-greeting.txt` on user storage with one short greeting
line. Safely eject, restart KOReader and enable or arrange the KindleLab Dashboard
module in SimpleUI's home-screen module settings. For MTP devices, check the
model-specific transfer instructions; paths or capabilities may differ.

The clock refreshes while the home screen is visible. The Wi-Fi name is read on
the Kindle and is not deliberately sent to the service. Layout and text sizes may
need adjustment for each display. Without a snapshot, weather and events show as
not connected.

## Optional local Wi-Fi sync (experimental)

The following creates a self-signed TLS certificate, private key and bearer token
in `artifacts/dashboard/lan`; it refuses to overwrite an existing identity. Review
the selected interface in the generated config; VPNs and multiple interfaces can
select the wrong route. A change of laptop IP requires updating the device host.

```powershell
.\.venv\Scripts\python.exe -m dashboard.prepare_lan
.\.venv\Scripts\python.exe -m dashboard.serve_lan
```

With KOReader closed and USB connected, create `kindlelab/lan/` on user storage.
Copy `server-cert.pem` and `token.txt` from the laptop's LAN directory there;
create `host.txt` containing just the selected local IPv4 address from the laptop's
LAN `config.json`. Keep `server-key.pem` on the laptop. Do not put the token,
private key, snapshots or configuration in Git. Safely eject and reopen KOReader.
The plugin tries every 15 minutes; `kindlelab/lan/status.txt` records `connected`
or `unavailable`. The laptop must remain running and reachable; a firewall may
block access. Never forward the port or expose this endpoint to the internet.

TLS verifies the configured certificate but the client does not separately verify
the server hostname. The bearer token is stored in user-accessible Kindle storage;
anyone with access to it can request calendar snapshots while the service runs.
Use a trusted local network and revoke/regenerate credentials if exposed. The LAN
sync has not been validated end-to-end in this portable version.

## Reading and appearance

Copy DRM-free EPUBs or PDFs to a folder on user storage and set that folder as
KOReader's home directory using its file browser. KOReader can configure its own
sleep screen and SimpleUI wallpaper; changes do not necessarily affect the stock
Kindle reader. Amazon books may use DRM or unsupported KFX; use the stock reader
for those and do not bypass DRM.

## Sharing safely

Only this curated kit and the root README are intended for Git. Local credentials,
tokens, personal snapshots, backups and the original device-specific project
history are excluded. Check `git status --short`, review the complete staged diff,
and scan for secrets and private details before publishing. Ignore rules do not
remove files already tracked or committed in a repository's history.
