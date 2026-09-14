import logging
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import reports, developers, settings, outlook, ai, email
from app.database import init_db
from app.config import settings as app_settings

# Only import scheduler if not on Vercel (serverless doesn't support background jobs)
IS_VERCEL = os.getenv("VERCEL") is not None
if not IS_VERCEL:
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

# ── CORS (allow React dev server and Vercel domains) ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://*.vercel.app",
        "https://jira-automation-git-main-ag-1a40.vercel.app"
    ],
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
    os.makedirs(app_settings.REPORT_STORAGE_PATH, exist_ok=True)
    os.makedirs(app_settings.UPLOAD_STORAGE_PATH, exist_ok=True)
    
    # Only configure scheduler for non-serverless environments
    if not IS_VERCEL:
        configure_scheduler()
    else:
        logger.info("Skipping scheduler on Vercel (serverless environment)")
    
    logger.info("DC-AI Reporting API ready.")


@app.on_event("shutdown")
def on_shutdown():
    if not IS_VERCEL:
        shutdown_scheduler()


@app.get("/")
def root():
    return {"message": "DC-AI Sprint Reporting API", "docs": "/docs"}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


# In the production container the React build is served by the same FastAPI
# process, which keeps the GitHub deployment to a single Render service.
# Skip this on Vercel where frontend is served separately.
if not IS_VERCEL:
    _frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend_dist"))
    if os.path.isdir(_frontend_dist):
        _assets_dir = os.path.join(_frontend_dist, "assets")
        if os.path.isdir(_assets_dir):
            app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend_app(path: str):
            requested = os.path.join(_frontend_dist, path)
            if path and os.path.isfile(requested):
                return FileResponse(requested)
            return FileResponse(os.path.join(_frontend_dist, "index.html"))
