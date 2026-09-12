import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import init_db

# Vercel does not reliably run ASGI lifespan startup hooks before invoking
# a serverless function, so ensure the ephemeral database schema exists.
init_db()
