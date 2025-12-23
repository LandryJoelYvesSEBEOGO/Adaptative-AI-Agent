# Guide d'Implémentation des APIs Backend

Ce document détaille les étapes pour créer toutes les APIs nécessaires pour connecter le frontend React au backend RAG Python.

## 📋 Table des matières

1. [Architecture API](#architecture-api)
2. [Installation des dépendances](#installation-des-dépendances)
3. [Structure du projet API](#structure-du-projet-api)
4. [APIs d'authentification](#apis-dauthentification)
5. [APIs de chat RAG](#apis-de-chat-rag)
6. [APIs du dashboard admin](#apis-du-dashboard-admin)
7. [APIs de feedback](#apis-de-feedback)
8. [Gestion CORS et middleware](#gestion-cors-et-middleware)
9. [Configuration et déploiement](#configuration-et-déploiement)
10. [Tests des APIs](#tests-des-apis)

---

## 🏗️ Architecture API

### Framework choisi : FastAPI

**Pourquoi FastAPI ?**
- Performance élevée
- Documentation automatique (Swagger/OpenAPI)
- Validation automatique avec Pydantic
- Support natif du streaming (Server-Sent Events)
- Compatible avec l'écosystème Python existant

### Structure des endpoints

```
/api/v1/
├── auth/
│   ├── POST /login
│   └── POST /logout
├── chat/
│   ├── POST /query
│   ├── POST /query/stream
│   └── POST /feedback
├── admin/
│   ├── GET /metrics/overview
│   ├── GET /metrics/requests
│   ├── GET /metrics/recent
│   ├── GET /metrics/errors
│   └── GET /system/status
```

---

## 📦 Installation des dépendances

### Étape 1 : Créer un fichier `requirements-api.txt`

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# CORS et sécurité
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# Validation et sérialisation
pydantic==2.5.0
pydantic-settings==2.1.0

# Utilitaires
aiofiles==23.2.1
```

### Étape 2 : Installer les dépendances

```bash
cd Backend
pip install -r requirements-api.txt
```

---

## 📁 Structure du projet API

### Structure recommandée

```
Backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # Point d'entrée FastAPI
│   │   ├── dependencies.py      # Dépendances (auth, etc.)
│   │   ├── middleware.py        # CORS, logging, etc.
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Routes d'authentification
│   │   │   ├── chat.py          # Routes de chat RAG
│   │   │   ├── admin.py         # Routes admin (métriques)
│   │   │   └── feedback.py      # Routes de feedback
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Modèles Pydantic pour auth
│   │   │   ├── chat.py          # Modèles pour chat
│   │   │   └── admin.py         # Modèles pour métriques
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py  # Logique d'authentification
│   │       ├── chat_service.py  # Logique de chat RAG
│   │       └── metrics_service.py # Logique de métriques
│   │
│   └── rag/
│       └── Rag_model.py         # (existant)
```

---

## 🔐 APIs d'authentification

### Étape 1 : Créer `src/api/models/auth.py`

```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    error: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str  # "admin" | "user"
```

### Étape 2 : Créer `src/api/services/auth_service.py`

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Base de données utilisateurs (à remplacer par une vraie DB)
MOCK_USERS = [
    {
        "id": "1",
        "email": "admin@rag-system.io",
        "hashed_password": pwd_context.hash("admin"),
        "name": "Admin User",
        "role": "admin"
    },
    {
        "id": "2",
        "email": "user@rag-system.io",
        "hashed_password": pwd_context.hash("user"),
        "name": "Standard User",
        "role": "user"
    }
]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(email: str) -> Optional[dict]:
    """Récupère un utilisateur par email."""
    for user in MOCK_USERS:
        if user["email"].lower() == email.lower():
            return user
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authentifie un utilisateur."""
    user = get_user_by_email(email)
    if not user:
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    # Retourner l'utilisateur sans le hash
    user_without_password = {k: v for k, v in user.items() if k != "hashed_password"}
    return user_without_password
```

### Étape 3 : Créer `src/api/routes/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from src.api.models.auth import LoginRequest, LoginResponse, UserResponse
from src.api.services.auth_service import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authentifie un utilisateur et retourne un token JWT.
    """
    user = authenticate_user(request.email, request.password)
    
    if not user:
        return LoginResponse(
            success=False,
            error="Email ou mot de passe incorrect"
        )
    
    # Créer le token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        success=True,
        token=access_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    )

@router.post("/logout")
async def logout():
    """
    Déconnecte un utilisateur (pour l'instant, juste une confirmation).
    En production, vous pourriez ajouter le token à une blacklist.
    """
    return {"success": True, "message": "Déconnecté avec succès"}
```

---

## 💬 APIs de chat RAG

### Étape 1 : Créer `src/api/models/chat.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class ChatQueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None  # Pour maintenir le contexte

class Citation(BaseModel):
    id: int
    source: str
    excerpt: str
    metadata: Optional[dict] = None

class ChatQueryResponse(BaseModel):
    response: str
    citations: List[Citation] = []
    conversation_id: str
    latency: Optional[float] = None
    success: bool = True
    error: Optional[str] = None

class FeedbackRequest(BaseModel):
    message_id: str
    feedback_type: str  # "thumbs_up" | "thumbs_down"
    comment: Optional[str] = None
```

### Étape 2 : Créer `src/api/services/chat_service.py`

```python
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import uuid

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.Rag_model import get_final_response, get_final_response_stream

def extract_citations(response_text: str) -> List[Dict]:
    """
    Extrait les citations de la réponse RAG.
    Format attendu: [1], [2], etc. dans le texte.
    """
    import re
    citations = []
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, response_text)
    
    # Pour l'instant, on retourne des citations génériques
    # Dans une implémentation complète, on récupérerait les vraies citations depuis le state RAG
    unique_ids = list(set(matches))
    for idx, citation_id in enumerate(unique_ids):
        citations.append({
            "id": int(citation_id),
            "source": f"Document {citation_id}",
            "excerpt": f"Extrait du document {citation_id}",
            "metadata": {}
        })
    
    return citations

def process_rag_query(question: str, conversation_id: Optional[str] = None) -> Dict:
    """
    Traite une question RAG et retourne la réponse.
    """
    import time
    
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    start_time = time.time()
    
    try:
        # Appeler la fonction RAG existante
        response_text = get_final_response(question)
        
        # Extraire les citations
        citations = extract_citations(response_text)
        
        latency = time.time() - start_time
        
        return {
            "response": response_text,
            "citations": citations,
            "conversation_id": conversation_id,
            "latency": latency,
            "success": True,
            "error": None
        }
    
    except Exception as e:
        latency = time.time() - start_time
        return {
            "response": "",
            "citations": [],
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "latency": latency,
            "success": False,
            "error": str(e)
        }

def process_rag_query_stream(question: str, conversation_id: Optional[str] = None):
    """
    Traite une question RAG en mode streaming.
    Retourne un générateur qui yield les chunks.
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    try:
        # Utiliser la fonction de streaming existante
        for chunk in get_final_response_stream(question):
            yield chunk
    
    except Exception as e:
        yield f"⚠️ Erreur lors de la génération: {str(e)}"
```

### Étape 3 : Créer `src/api/routes/chat.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from src.api.models.chat import ChatQueryRequest, ChatQueryResponse, FeedbackRequest
from src.api.services.chat_service import process_rag_query, process_rag_query_stream
import json

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/query", response_model=ChatQueryResponse)
async def query_rag(request: ChatQueryRequest):
    """
    Traite une question RAG et retourne la réponse complète.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")
    
    result = process_rag_query(
        question=request.question,
        conversation_id=request.conversation_id
    )
    
    return ChatQueryResponse(**result)

@router.post("/query/stream")
async def query_rag_stream(request: ChatQueryRequest):
    """
    Traite une question RAG en mode streaming (Server-Sent Events).
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide")
    
    def generate_stream():
        for chunk in process_rag_query_stream(
            question=request.question,
            conversation_id=request.conversation_id
        ):
            # Format SSE (Server-Sent Events)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Enregistre le feedback utilisateur (thumbs up/down).
    """
    # TODO: Enregistrer le feedback dans une base de données
    # Pour l'instant, on retourne juste une confirmation
    
    return {
        "success": True,
        "message": "Feedback enregistré avec succès",
        "message_id": request.message_id,
        "feedback_type": request.feedback_type
    }
```

---

## 📊 APIs du dashboard admin

### Étape 1 : Créer `src/api/models/admin.py`

```python
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class MetricOverview(BaseModel):
    total_requests: int
    requests_today: int
    success_rate: float  # En pourcentage
    average_latency: float  # En secondes
    error_count: int

class RequestDataPoint(BaseModel):
    date: str
    requests: int
    success: int
    errors: int

class ErrorDistribution(BaseModel):
    timeout: int
    llm_error: int
    retrieval: int
    web_search: int
    other: int

class RecentRequest(BaseModel):
    id: str
    timestamp: str
    user: str
    question: str
    status: str  # "success" | "error"
    latency: float

class SystemStatus(BaseModel):
    rag_pipeline: str  # "Active" | "Inactive"
    vector_db: str     # "Connected" | "Disconnected"
    llm_status: str    # "Operational" | "Degraded" | "Down"
    uptime_percentage: float
```

### Étape 2 : Créer `src/api/services/metrics_service.py`

```python
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Chemin vers le fichier de métriques
METRICS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "metrics" / "metrics.jsonl"
SUMMARY_FILE = Path(__file__).parent.parent.parent.parent / "data" / "metrics" / "summary.json"

def load_metrics_summary() -> Dict:
    """Charge le résumé des métriques."""
    if not SUMMARY_FILE.exists():
        return {
            "total_requests": 0,
            "total_errors": 0,
            "latencies": {"end_to_end": []},
            "last_updated": datetime.now().isoformat()
        }
    
    with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_recent_requests(limit: int = 50) -> List[Dict]:
    """Charge les requêtes récentes depuis le fichier JSONL."""
    requests = []
    
    if not METRICS_FILE.exists():
        return []
    
    # Lire les dernières lignes du fichier
    with open(METRICS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Prendre les N dernières lignes
    for line in lines[-limit:]:
        try:
            request_data = json.loads(line.strip())
            requests.append(request_data)
        except json.JSONDecodeError:
            continue
    
    # Trier par timestamp (plus récent en premier)
    requests.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return requests[:limit]

def calculate_today_metrics() -> Dict:
    """Calcule les métriques du jour."""
    today = datetime.now().date().isoformat()
    requests = load_recent_requests(limit=1000)
    
    today_requests = [
        req for req in requests
        if req.get("timestamp", "").startswith(today)
    ]
    
    successful = sum(1 for req in today_requests if req.get("success", False))
    errors = len(today_requests) - successful
    
    latencies = [
        req.get("latencies", {}).get("end_to_end", 0)
        for req in today_requests
        if req.get("success", False) and req.get("latencies", {}).get("end_to_end")
    ]
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    success_rate = (successful / len(today_requests) * 100) if today_requests else 0.0
    
    return {
        "count": len(today_requests),
        "success": successful,
        "errors": errors,
        "success_rate": success_rate,
        "average_latency": avg_latency
    }

def get_metrics_overview() -> Dict:
    """Retourne un aperçu des métriques."""
    summary = load_metrics_summary()
    today_metrics = calculate_today_metrics()
    
    total_requests = summary.get("total_requests", 0)
    total_errors = summary.get("total_errors", 0)
    
    # Calculer la latence moyenne globale
    end_to_end_latencies = summary.get("latencies", {}).get("end_to_end", [])
    avg_latency = sum(end_to_end_latencies) / len(end_to_end_latencies) if end_to_end_latencies else 0.0
    
    # Taux de succès global
    global_success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0.0
    
    return {
        "total_requests": total_requests,
        "requests_today": today_metrics["count"],
        "success_rate": global_success_rate,
        "average_latency": avg_latency,
        "error_count": total_errors
    }

def get_requests_chart_data(days: int = 7) -> List[Dict]:
    """Retourne les données pour le graphique des requêtes."""
    requests = load_recent_requests(limit=10000)
    
    # Grouper par date
    date_groups: Dict[str, Dict] = {}
    
    for req in requests:
        timestamp = req.get("timestamp", "")
        if not timestamp:
            continue
        
        date = timestamp[:10]  # YYYY-MM-DD
        
        if date not in date_groups:
            date_groups[date] = {"requests": 0, "success": 0, "errors": 0}
        
        date_groups[date]["requests"] += 1
        if req.get("success", False):
            date_groups[date]["success"] += 1
        else:
            date_groups[date]["errors"] += 1
    
    # Convertir en liste et formater les dates
    result = []
    for date, data in sorted(date_groups.items(), reverse=True)[:days]:
        # Formater la date (ex: "22 Dec")
        date_obj = datetime.fromisoformat(date)
        formatted_date = date_obj.strftime("%d %b")
        
        result.insert(0, {
            "date": formatted_date,
            "requests": data["requests"],
            "success": data["success"],
            "errors": data["errors"]
        })
    
    return result

def get_error_distribution() -> Dict:
    """Retourne la répartition des erreurs."""
    requests = load_recent_requests(limit=1000)
    
    distribution = {
        "timeout": 0,
        "llm_error": 0,
        "retrieval": 0,
        "web_search": 0,
        "other": 0
    }
    
    for req in requests:
        if not req.get("success", False):
            error = req.get("error", "").lower()
            
            if "timeout" in error:
                distribution["timeout"] += 1
            elif "llm" in error or "generation" in error:
                distribution["llm_error"] += 1
            elif "retrieval" in error or "retrieve" in error:
                distribution["retrieval"] += 1
            elif "web" in error or "search" in error:
                distribution["web_search"] += 1
            else:
                distribution["other"] += 1
    
    return distribution

def get_system_status() -> Dict:
    """Retourne le statut du système."""
    # Pour l'instant, on retourne un statut statique
    # Dans une implémentation complète, on vérifierait la connexion à la DB vectorielle, etc.
    
    return {
        "rag_pipeline": "Active",
        "vector_db": "Connected",
        "llm_status": "Operational",
        "uptime_percentage": 98.5
    }
```

### Étape 3 : Créer `src/api/routes/admin.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from src.api.models.admin import (
    MetricOverview,
    RequestDataPoint,
    ErrorDistribution,
    RecentRequest,
    SystemStatus
)
from src.api.services.metrics_service import (
    get_metrics_overview,
    get_requests_chart_data,
    get_error_distribution,
    get_system_status,
    load_recent_requests
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# TODO: Ajouter une dépendance d'authentification pour vérifier le role "admin"
# from src.api.dependencies import require_admin

@router.get("/metrics/overview", response_model=MetricOverview)
async def get_overview():
    """
    Retourne un aperçu des métriques du système.
    """
    # await require_admin()  # À décommenter une fois l'auth implémentée
    
    overview = get_metrics_overview()
    return MetricOverview(**overview)

@router.get("/metrics/requests", response_model=List[RequestDataPoint])
async def get_requests_metrics(days: Optional[int] = 7):
    """
    Retourne les données pour le graphique des requêtes.
    """
    # await require_admin()
    
    chart_data = get_requests_chart_data(days=days)
    return [RequestDataPoint(**item) for item in chart_data]

@router.get("/metrics/recent", response_model=List[RecentRequest])
async def get_recent_requests(limit: Optional[int] = 50):
    """
    Retourne les requêtes récentes.
    """
    # await require_admin()
    
    requests = load_recent_requests(limit=limit)
    
    # Formater pour correspondre au modèle
    formatted_requests = []
    for req in requests:
        formatted_requests.append({
            "id": req.get("conversation_id", "unknown"),
            "timestamp": req.get("timestamp", ""),
            "user": "user@rag-system.io",  # TODO: Récupérer depuis le token JWT
            "question": req.get("query", "")[:100],
            "status": "success" if req.get("success", False) else "error",
            "latency": req.get("latencies", {}).get("end_to_end", 0.0)
        })
    
    return [RecentRequest(**req) for req in formatted_requests]

@router.get("/metrics/errors", response_model=ErrorDistribution)
async def get_error_distribution_endpoint():
    """
    Retourne la répartition des erreurs.
    """
    # await require_admin()
    
    distribution = get_error_distribution()
    return ErrorDistribution(**distribution)

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status_endpoint():
    """
    Retourne le statut du système.
    """
    # await require_admin()
    
    status = get_system_status()
    return SystemStatus(**status)
```

---

## 🔄 Gestion CORS et middleware

### Étape 1 : Créer `src/api/middleware.py`

```python
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
```

### Étape 2 : Créer `src/api/dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from src.api.services.auth_service import SECRET_KEY

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dépendance pour récupérer l'utilisateur actuel depuis le token JWT.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        return {"email": email, "role": role}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )

async def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dépendance pour vérifier que l'utilisateur est admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    
    return current_user
```

---

## 🚀 Configuration et déploiement

### Étape 1 : Créer `src/api/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import des routers
from src.api.routes import auth, chat, admin, feedback
from src.api.middleware import setup_cors

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer l'application FastAPI
app = FastAPI(
    title="RAG System API",
    description="API pour le système RAG avec frontend React",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurer CORS
setup_cors(app)

# Inclure les routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(feedback.router)

@app.get("/")
async def root():
    """Endpoint racine."""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### Étape 2 : Créer les fichiers `__init__.py`

**`src/api/__init__.py`** (vide ou avec imports)

**`src/api/routes/__init__.py`**:
```python
from . import auth, chat, admin, feedback

__all__ = ["auth", "chat", "admin", "feedback"]
```

**`src/api/models/__init__.py`** (vide)

**`src/api/services/__init__.py`** (vide)

### Étape 3 : Créer un script de démarrage `Backend/run_api.py`

```python
#!/usr/bin/env python
"""
Script pour démarrer l'API FastAPI.
"""
import uvicorn
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "src")],
        log_level="info"
    )
```

### Étape 4 : Lancer l'API

```bash
cd Backend
python run_api.py
```

L'API sera accessible sur :
- **API**: http://localhost:8000
- **Documentation Swagger**: http://localhost:8000/api/docs
- **Documentation ReDoc**: http://localhost:8000/api/redoc

---

## 🧪 Tests des APIs

### Étape 1 : Tester avec curl

```bash
# Test de l'endpoint de santé
curl http://localhost:8000/health

# Test de login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@rag-system.io", "password": "admin"}'

# Test de chat (avec token)
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"question": "Qu'est-ce que le RAG?"}'

# Test des métriques admin
curl http://localhost:8000/api/v1/admin/metrics/overview \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Étape 2 : Tester avec la documentation Swagger

1. Ouvrir http://localhost:8000/api/docs
2. Cliquer sur un endpoint
3. Cliquer sur "Try it out"
4. Remplir les paramètres
5. Cliquer sur "Execute"

---

## 🔗 Intégration Frontend

### Étape 1 : Créer `Frontend/src/services/api.ts`

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Erreur réseau' }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string) {
    return this.request<{ success: boolean; token?: string; user?: any }>(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );
  }

  async logout() {
    return this.request('/auth/logout', { method: 'POST' });
  }

  // Chat
  async queryRAG(question: string, conversationId?: string) {
    return this.request<{
      response: string;
      citations: any[];
      conversation_id: string;
      latency?: number;
    }>('/chat/query', {
      method: 'POST',
      body: JSON.stringify({ question, conversation_id: conversationId }),
    });
  }

  async queryRAGStream(
    question: string,
    conversationId: string | undefined,
    onChunk: (chunk: string) => void
  ) {
    const url = `${this.baseURL}/chat/query/stream`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ question, conversation_id: conversationId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Stream non disponible');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.chunk) {
              onChunk(parsed.chunk);
            }
          } catch (e) {
            // Ignorer les erreurs de parsing
          }
        }
      }
    }
  }

  async submitFeedback(messageId: string, feedbackType: 'thumbs_up' | 'thumbs_down', comment?: string) {
    return this.request('/chat/feedback', {
      method: 'POST',
      body: JSON.stringify({
        message_id: messageId,
        feedback_type: feedbackType,
        comment,
      }),
    });
  }

  // Admin
  async getMetricsOverview() {
    return this.request('/admin/metrics/overview');
  }

  async getRequestsMetrics(days: number = 7) {
    return this.request(`/admin/metrics/requests?days=${days}`);
  }

  async getRecentRequests(limit: number = 50) {
    return this.request(`/admin/metrics/recent?limit=${limit}`);
  }

  async getErrorDistribution() {
    return this.request('/admin/metrics/errors');
  }

  async getSystemStatus() {
    return this.request('/admin/system/status');
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
```

---

## ✅ Checklist de déploiement

- [ ] Installer toutes les dépendances (`requirements-api.txt`)
- [ ] Créer tous les fichiers de structure
- [ ] Configurer les variables d'environnement (JWT_SECRET_KEY, etc.)
- [ ] Tester tous les endpoints avec Swagger
- [ ] Configurer CORS pour les origines frontend
- [ ] Implémenter l'authentification JWT complète
- [ ] Intégrer le service API dans le frontend
- [ ] Tester le streaming du chat
- [ ] Tester les métriques admin
- [ ] Configurer le logging et la gestion d'erreurs
- [ ] Déployer sur un serveur de production (optionnel)

---

## 📝 Notes importantes

1. **Sécurité** : Changez `SECRET_KEY` en production et utilisez des variables d'environnement
2. **Base de données** : Les utilisateurs sont actuellement en dur, il faudra intégrer une vraie DB
3. **Métriques** : Les métriques sont lues depuis des fichiers JSONL, envisagez une DB pour la production
4. **Streaming** : Le streaming utilise Server-Sent Events (SSE), compatible avec la plupart des navigateurs
5. **Authentification** : L'auth est basique, envisagez refresh tokens pour la production

---

## 🆘 Dépannage

### Erreur "Module not found"
- Vérifiez que tous les `__init__.py` existent
- Vérifiez les chemins d'import dans `sys.path`

### CORS errors
- Vérifiez que les origines frontend sont bien listées dans `setup_cors`
- Vérifiez que le frontend envoie bien les credentials

### Token JWT invalide
- Vérifiez que `SECRET_KEY` est le même partout
- Vérifiez l'expiration du token

### Streaming ne fonctionne pas
- Vérifiez que le frontend gère bien les Server-Sent Events
- Vérifiez les headers CORS pour SSE

