from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.database import init_db
from app.routes import about, auth, notes, web

init_db()

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Notes API",
    version="1.0.0",
    description="REST API with JWT Bearer authentication (access + refresh tokens).",
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(web.router)
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(about.router)
