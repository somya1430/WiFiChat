# Backend

Run the API from the project root:

```powershell
myenv\Scripts\pip install -r backend\requirements.txt
set CHAT_SECRET_KEY=replace-with-a-long-random-secret
myenv\Scripts\uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The SQLite database is created automatically as `backend/wifi_chat.db` when the API starts.

If you ran the Phase 1 prototype, delete `backend/wifi_chat.db` before first starting Phase 2. The old database contains temporary identities without password hashes and cannot be migrated into accounts.

Interactive API documentation is available at `http://localhost:8000/docs`.

For development, the server has a fallback JWT secret. Set `CHAT_SECRET_KEY` before sharing the app on a network or deploying it.
