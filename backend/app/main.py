"""Jansaarthi central backend. Run:  uvicorn app.main:app --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import ROOT, settings
from .db import init_db
from .errors import install_handlers
from .routers import ai, auth, complaints, media, print_history, system
from .services import ocr


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ocr.log_status()
    yield


app = FastAPI(title="Jansaarthi Backend", version="1.0.0", lifespan=lifespan,
              description="Central API for the kiosk: login, speech, OCR, translation, AI queries, "
                          "complaints, printing, history and health.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_methods=["*"], allow_headers=["*"])
install_handlers(app)
for r in (auth, media, ai, complaints, print_history, system):
    app.include_router(r.router)

# Kiosk mode: if the UI has been built (cd frontend && npm run build), serve it from the same port.
_dist = ROOT.parent / "frontend" / "dist"
if _dist.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_dist, html=True), name="ui")