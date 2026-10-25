# Backend

Run the API from the project root:

```powershell
myenv\Scripts\pip install -r backend\requirements.txt
myenv\Scripts\uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The SQLite database is created automatically as `backend/wifi_chat.db` when the API starts.

Interactive API documentation is available at `http://localhost:8000/docs`.
