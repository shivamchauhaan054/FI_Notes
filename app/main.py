from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.database import init_db
from app.routes import about, auth, notes, web

init_db()

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="FI Notes — Enterprise Grade REST API",
    version="1.5.0",
    description="""
A secure, multi-user note-taking platform featuring:
- **JWT Authentication** (Access & Refresh tokens)
- **Google OAuth 2.0** Integration
- **Bilingual Support** (Phonetic Hindi Transliteration)
- **Note Version History** (Automatic archiving)
- **Pinning & Search** (Optimized for performance)
- **SMTP OTP Verification** (MFA security)
    """,
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(web.router)
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(about.router)

@app.get("/search", response_model=list[notes.NoteResponse], tags=["search"])
def search_redirect(results=Depends(notes.search_notes)):
    return results
@app.get("/")
def root():
    return {"message": "FI Notes Backend Running"}  

@app.get("/health")
def health():
    return {"status": "ok"}