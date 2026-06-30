# Deployment Guide

Voice2Justice is designed to be easily deployable on modern Platform-as-a-Service (PaaS) providers like Render, Heroku, or Railway.

## 1. Render Deployment (Recommended)

The repository includes a `render.yaml` infrastructure-as-code file which automates deployment on Render.

### Prerequisites
1. Push the code to a GitHub repository.
2. Sign up for a Render account.
3. Configure Google OAuth credentials in Google Cloud Console.
4. Generate a Gmail App Password.

### Deployment Steps
1. In Render, create a new **Blueprint Instance**.
2. Connect your GitHub repository.
3. Render will read the `render.yaml` file and automatically provision a Python Web Service.
4. Go to the Environment section of your new Web Service and manually add the secrets that are set to `sync: false` in the YAML file:
   - `EMAIL_USER`
   - `EMAIL_PASS`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

### Gunicorn Configuration
The deployment uses Gunicorn as the WSGI HTTP Server. The start command is configured as:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```
- **`--workers 2`**: Ensures the server can handle concurrent requests.
- **`--timeout 120`**: Prevents Gunicorn from killing worker processes during heavy ML inference or PDF generation if the system is under load.

## 2. Ephemeral Filesystem Warning (SQLite)

> **⚠️ WARNING**: PaaS free tiers (like Render or Heroku) use ephemeral filesystems. This means that every time your server restarts or deploys a new update, the `complaints.db` SQLite file and `reports/` PDF cache will be wiped.

### For Production
If deploying for real-world production use, you must migrate the database URI to a managed PostgreSQL instance.
In `flask/models/db.py`, replace the `sqlite3` connection with `psycopg2` or an ORM like SQLAlchemy connected to a `DATABASE_URL` environment variable.

## 3. Google OAuth Configuration

When deploying to a live URL (e.g., `https://voice2justicee.onrender.com`), you MUST update the Google Cloud Console:
1. Go to **APIs & Services > Credentials**.
2. Edit your OAuth 2.0 Client ID.
3. Under **Authorized redirect URIs**, add your production callback URL:
   `https://voice2justicee.onrender.com/user/login/google/callback`
4. If you miss this step, Google will throw a `redirect_uri_mismatch` error when users attempt to log in.
