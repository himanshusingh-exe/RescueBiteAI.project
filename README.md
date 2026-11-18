# RescueBite AI — Starter Project

This starter preserves the existing HTML frontend and adds a minimal Flask backend.

## Folder structure

- `frontend/` — the existing HTML pages
- `backend/app.py` — Flask server and first API endpoint
- `backend/requirements.txt` — Python dependencies

## Run on Windows

1. Install Python 3 if it is not already installed. During installation, check **Add Python to PATH**.
2. Open this folder in VS Code.
3. Open Terminal and run:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

4. Open these addresses in your browser:
   - Website: http://127.0.0.1:5000
   - Backend test: http://127.0.0.1:5000/api/health

The health endpoint should return JSON showing that the backend is running.

**This is only the starting scaffold.** The database, login, donation APIs, and AI features will be added in later steps.
