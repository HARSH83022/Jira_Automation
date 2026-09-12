import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import reports, developers, settings, outlook, ai, email
from app.database import init_db
from app.services.scheduler import configure_scheduler, shutdown_scheduler

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DC-AI Sprint Reporting API",
    description="Automated sprint development report generation from Jira CSV exports.",
    version="1.0.0",
)

# ── CORS (allow React dev server) ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(reports.router)
app.include_router(developers.router)
app.include_router(settings.router)
app.include_router(outlook.router)
app.include_router(ai.router)
app.include_router(email.router)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("Initialising database…")
    init_db()
    os.makedirs("./generated_reports", exist_ok=True)
    os.makedirs("./uploads", exist_ok=True)
    configure_scheduler()
    logger.info("DC-AI Reporting API ready.")


@app.on_event("shutdown")
def on_shutdown():
    shutdown_scheduler()


@app.get("/")
def root():
    return {"message": "DC-AI Sprint Reporting API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
