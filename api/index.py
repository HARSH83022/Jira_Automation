import os
import sys

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Initialize database before importing app
from app.database import init_db
init_db()

# Now import the FastAPI app
from app.main import app

# Vercel serverless handler
handler = app
