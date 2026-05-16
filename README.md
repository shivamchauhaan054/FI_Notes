# FI Notes

Production-ready REST API for a multi-user FI Notes application built with FastAPI, SQLAlchemy, and SQLite.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy ORM
- SQLite
- Pydantic
- JWT authentication (python-jose)
- Password hashing (passlib + bcrypt)
- Uvicorn
- Dark/Light mode support (System preference + Toggle)
- Bilingual (English/Hindi) note support with real-time transliteration

## Project Structure

```
app/
 ├── main.py
 ├── database.py
 ├── models/
 ├── schemas/
 ├── routes/
 ├── services/
 ├── core/
 ├── dependencies/
 └── utils/
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file and update values as needed:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

**Web app (UI):** http://127.0.0.1:8000/  
Interactive docs: `http://127.0.0.1:8000/docs`  
OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

### Port already in use (WinError 10013)

If you see `[WinError 10013]`, port `8000` is likely already taken by another process. Either stop it:

```powershell
netstat -ano | findstr ":8000"
taskkill /PID <PID_FROM_ABOVE> /F
```

Or run on a different port:

```powershell
uvicorn app.main:app --reload --port 8001
```

## Authentication setup (required for full flow)

### Email OTP (SMTP)

Use Gmail with an [App Password](https://myaccount.google.com/apppasswords), or any SMTP provider:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your.email@gmail.com
SMTP_USE_TLS=true
```

If SMTP is not configured, OTP codes are printed in the server console. For local testing without email, set `DEV_SHOW_OTP=true` in `.env` to return the code in the register API response.

### Google sign-in

1. Open [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add authorized redirect URI: `http://127.0.0.1:8000/auth/google/callback`
4. Add to `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
FRONTEND_URL=http://127.0.0.1:8000
```

### Auth flow

1. **Email register** → 6-digit OTP emailed → verify → JWT issued  
2. **Email login** → if unverified, new OTP sent → verify screen  
3. **Google** → one-click sign-in (email pre-verified by Google)

**Upgrading an old database:** delete `notes.db` and restart, or the app will auto-migrate columns on startup.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register; sends email OTP |
| POST | `/verify-otp` | No | Verify OTP; returns JWT |
| POST | `/resend-otp` | No | Resend verification code |
| POST | `/login` | No | Login (email must be verified) |
| GET | `/auth/google` | No | Start Google OAuth |
| GET | `/auth/status` | No | Check OAuth/SMTP config |
| GET | `/notes` | Bearer | List own notes |
| GET | `/notes/{id}` | Bearer | Get note (owner or shared) |
| POST | `/notes` | Bearer | Create a note |
| PUT | `/notes/{id}` | Bearer | Update note (owner only) |
| DELETE | `/notes/{id}` | Bearer | Delete note (owner only) |
| POST | `/notes/{id}/share` | Bearer | Share note with another user |
| GET | `/about` | No | API author information |

## Authentication

Protected routes require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain a token by calling `POST /login` with valid credentials.

## Example Usage

### Register

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"user@example.com\", \"password\": \"password123\"}"
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"user@example.com\", \"password\": \"password123\"}"
```

### Create a note

```bash
curl -X POST http://127.0.0.1:8000/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"title\": \"My Note\", \"content\": \"Note content here\"}"
```
