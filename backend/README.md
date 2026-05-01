Backend for Test1 Admin UI

Run locally:

1. Create and activate a Python virtualenv.
2. Install requirements: `pip install -r backend/requirements.txt`
3. From the project root run: `python backend/app.py`

The Flask app serves the static UI from the `sky` folder and exposes API endpoints under `/api`.

SMTP (optional)
 - To enable actual email delivery for password resets, set the following environment variables before starting the server:
	 - `SMTP_HOST` (required to enable sending)
	 - `SMTP_PORT` (optional, default 587)
	 - `SMTP_USER` (optional, used for login and sender address if `SMTP_FROM` not set)
	 - `SMTP_PASS` (optional, SMTP password)
	 - `SMTP_FROM` (optional, email address shown in From header)
	 - `SMTP_TLS` (optional, 'true' or 'false', default true)

Example (PowerShell):
```powershell
$env:SMTP_HOST='smtp.example.com'
$env:SMTP_PORT='587'
$env:SMTP_USER='no-reply@example.com'
$env:SMTP_PASS='supersecret'
$env:SMTP_FROM='no-reply@example.com'
python backend/app.py
```

If SMTP is not configured, password reset links are logged to the server console and appended to `backend/reset_links.jsonl` for local retrieval (dev only).
