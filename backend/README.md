# Backend for Test1 Admin UI

Flask-based backend with SQLAlchemy ORM, session-based authentication, and opportunity management.

## Quick Start

### 1. Setup Local Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment (Optional)

Copy `backend/.env.example` to `backend/.env` and update as needed:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your settings (database URL, SMTP credentials, etc.).

### 3. Run the Server

```bash
python backend/app.py
```

The Flask app serves the static UI from the `sky/` folder and exposes REST API endpoints under `/api/`.

- **UI Home**: http://127.0.0.1:5000/
- **Debug Mode**: Enabled (auto-reload on file changes)
- **Database**: SQLite (`backend/data.db` auto-created on startup)

## Environment Variables

All optional unless otherwise noted. See `backend/.env.example` for a template.

- `FLASK_ENV` — 'development' or 'production'
- `FLASK_DEBUG` — 1 or 0
- `SECRET_KEY` — used for session signing and token generation (default: 'dev-secret-key')
- `DATABASE_URL` — SQLite connection string (default: sqlite:///data.db)

### SMTP Configuration (Optional)

To enable email delivery for password reset links, set:

- `SMTP_HOST` — SMTP server hostname (e.g., smtp.mailtrap.io)
- `SMTP_PORT` — SMTP port (default: 587)
- `SMTP_USER` — SMTP username
- `SMTP_PASS` — SMTP password
- `SMTP_FROM` — sender email address (default: SMTP_USER)
- `SMTP_TLS` — enable TLS (default: true)

If SMTP is not configured, reset links are logged to console and saved to `backend/reset_links.jsonl` (dev only).

#### Example (PowerShell with Mailtrap):

```powershell
$env:SMTP_HOST='smtp.mailtrap.io'
$env:SMTP_PORT='587'
$env:SMTP_USER='your_mailtrap_username'
$env:SMTP_PASS='your_mailtrap_password'
$env:SMTP_FROM='noreply@example.com'
python backend/app.py
```

#### Example (PowerShell with .env file):

```powershell
# Edit backend/.env, then run
python backend/app.py
```

## API Endpoints

### Authentication

- `POST /api/signup` — Create a new admin account
- `POST /api/login` — Login and set session cookie
- `POST /api/logout` — Clear session
- `POST /api/forgot` — Send password reset link
- `GET /api/reset/<token>` — Validate reset token
- `POST /api/reset/<token>` — Set new password

### Opportunities

- `GET /api/opportunities` — List all opportunities for logged-in admin
- `POST /api/opportunities` — Create a new opportunity
- `GET /api/opportunities/<id>` — Get opportunity details
- `PUT /api/opportunities/<id>` — Update an opportunity
- `DELETE /api/opportunities/<id>` — Delete an opportunity

All opportunity endpoints require a valid session (login).

## Models

### Admin

- `id` (int, primary key)
- `email` (str, unique)
- `password_hash` (str)
- `name` (str)
- `created_at` (datetime)

### Opportunity

- `id` (int, primary key)
- `admin_id` (int, foreign key to Admin)
- `name` (str)
- `duration` (str)
- `start_date` (str)
- `description` (str)
- `skills` (JSON list)
- `category` (str)
- `future_opportunities` (str)
- `max_applicants` (int, nullable)
- `created_at` (datetime)

## Development Helpers

- `GET /api/debug/reset-links` — (dev only) Retrieve all reset links from `backend/reset_links.jsonl`

## Deployment

For production:

1. Set `FLASK_ENV=production` and `FLASK_DEBUG=0`
2. Use a production WSGI server (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
   ```
3. Set a strong `SECRET_KEY`
4. Use a production database (e.g., PostgreSQL)
5. Configure SMTP for email delivery
