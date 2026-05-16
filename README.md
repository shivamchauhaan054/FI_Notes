# FI Notes — Your Thoughts, Reimagined

FI Notes is a secure, enterprise-grade note-taking platform built with **FastAPI** and **Modern Glassmorphism UI**. It features multi-user support, bilingual phonetic transliteration, and robust note management tools.

![Project Status](https://img.shields.io/badge/Status-Production--Ready-success)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![Aesthetic](https://img.shields.io/badge/UI-Premium--Glassmorphism-6366f1)

---

## ✨ Key Features

- 🔐 **Dual Authentication**: Secure login via **Google OAuth 2.0** or traditional Email/Password with **SMTP OTP Verification**.
- 🇮🇳 **Bilingual Support**: Real-time phonetic Hindi transliteration (type in English, see Hindi).
- 📌 **Note Management**: Pin important notes to the top and stay organized.
- 🕒 **Version History**: Automatic archiving of previous note states whenever you update.
- 🤝 **Secure Sharing**: Share notes with other registered users in one click.
- 🌓 **Adaptive UI**: High-fidelity dark and light mode with system-preference detection.
- 🛡️ **Security First**: JWT-based session management with access and refresh tokens.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+)
- **Security**: JWT, Passlib (Bcrypt), Google OAuth 2.0
- **Communications**: SMTP for Multi-Factor Authentication (MFA)

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- A Google Cloud Project (for OAuth, optional)
- An SMTP account (Gmail App Password recommended)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/shivamchauhaan054/FI_Notes.git
cd FI_Notes

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
# Core Security
SECRET_KEY=your_super_secret_key_here
ALGORITHM=HS256

# SMTP Configuration (for OTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your.email@gmail.com

# Google OAuth (Optional but recommended)
GOOGLE_CLIENT_ID=your_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback

# URLs
FRONTEND_URL=http://127.0.0.1:8000
```

### 4. Running Locally
```bash
uvicorn app.main:app --reload
```
Access the application at `http://127.0.0.1:8000`

---

## 📖 API Documentation

The project includes built-in interactive documentation:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 🚢 Production Deployment

For production environments, use **Gunicorn** with the Uvicorn worker:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app
```

*Note: If deploying with SQLite, ensure you use a persistent disk for the `notes.db` file to prevent data loss on restarts.*

---

## 👨‍💻 Author
**Shivam Chauhan**  
[GitHub](https://github.com/shivamchauhaan054) | [Email](mailto:22bme054@iiitdmj.ac.in)

Built with ❤️ for better note-taking.
