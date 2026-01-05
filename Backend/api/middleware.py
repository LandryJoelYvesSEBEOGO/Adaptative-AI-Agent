from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

def setup_cors(app):
    """Configure CORS pour permettre les requêtes depuis le frontend."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative port
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

async def log_requests(request: Request, call_next):
    """Middleware pour logger les requêtes."""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response