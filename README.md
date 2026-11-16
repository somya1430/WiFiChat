# Wi-Fi Chat

A room-based chat application for people on the same local network. Users can create an account, join or create chat rooms, exchange messages instantly, and see who is currently online in the room.

## Features

- Account registration and sign-in with securely hashed passwords
- JWT-based authentication for protected chat actions
- Create and join public chat rooms
- Real-time messages over WebSockets
- Live participant list for the active room
- Persistent message history using SQLite
- Responsive React interface
- Local-network access for phones and computers connected to the same Wi-Fi

## Technology

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, JavaScript, CSS |
| Backend | FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy |
| Authentication | JWT and bcrypt |
| Real-time communication | WebSockets |

## Project structure

```text
backend/
  app/                 FastAPI routes, database models, auth, and presence
  requirements.txt     Backend dependencies
frontend/
  src/                 React application source
  package.json         Frontend scripts and dependencies
static/                Legacy prototype UI assets
main.py                Legacy prototype server
```

The active full-stack application is in `backend/` and `frontend/`. The root `main.py` and `static/` folder are retained from the original prototype and are not used by the React/FastAPI app.

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer with npm
- Two terminal windows

## Run locally

### 1. Start the backend

From the project root, create or activate a Python virtual environment, then install the backend packages:

```powershell
myenv\Scripts\pip install -r backend\requirements.txt
```

Set a strong token-signing secret for the current PowerShell session:

```powershell
$env:CHAT_SECRET_KEY = "replace-this-with-a-long-random-secret"
```

Start FastAPI:

```powershell
myenv\Scripts\uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Start the frontend

Open another terminal at the project root:

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open [http://localhost:5173](http://localhost:5173) on the host computer.

## Use from another device on the same Wi-Fi

1. Keep both development servers running on the host computer.
2. Find the host computer's Wi-Fi IPv4 address:

   ```powershell
   ipconfig
   ```

3. On another device connected to the same Wi-Fi, open `http://<HOST-IP>:5173`.

   For example: `http://192.168.1.25:5173`.

4. Allow Node.js/Vite through Windows Firewall on private networks if Windows asks.

The Vite server forwards `/api` and WebSocket traffic to FastAPI, so users only need the frontend address on port `5173`.

## First-time use and accounts

1. Open the app.
2. Choose **Create account**.
3. Sign in with the new username and password.
4. Create a room or select an existing room to join it.
5. Send messages and view the live participant list.

## Database notes

SQLite data is stored in `backend/wifi_chat.db` and is ignored by Git.

If you previously ran the Phase 1 prototype, remove that local database before using this version. Phase 1 used temporary identities, so its data cannot be migrated into password-based accounts.

## Development commands

Build the frontend for production:

```powershell
cd frontend
npm run build
```

Install the backend development/test dependencies:

```powershell
myenv\Scripts\pip install -r backend\requirements-dev.txt
```

## Current limitations

- Presence is stored in memory, so it is designed for one FastAPI server process.
- SQLite is ideal for local development and small LAN use; a hosted deployment should use PostgreSQL.
- A multi-server deployment should use Redis for shared WebSocket presence and rate limiting.
- Rooms are public in the current version; passcode-protected rooms and moderation tools are future enhancements.
