# Patch bcrypt pour passlib - DOIT être importé en premier
from api.services.bcrypt_patch import *  # noqa: F401, F403

from fastapi import FastAPI
import logging

# Import des routers
from api.routes import auth, chat, admin
from api.middleware import setup_cors, log_requests

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="RAG System API",
    description="API pour le système RAG avec frontend React",
    version="1.0.0",
    docs_url="/docs",  # URL par défaut de FastAPI
    redoc_url="/redoc"  # URL par défaut de ReDoc
)

# Configurer CORS
setup_cors(app)

# Ajouter le middleware de logging
app.middleware("http")(log_requests)

# Inclure les routers
app.include_router(auth.router)
app.include_router(chat.router)  # Inclut aussi /feedback
app.include_router(admin.router)

@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",  # Utiliser 127.0.0.1 au lieu de 0.0.0.0 pour Windows
        port=8000,
        reload=True
    )