import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Chemin vers le fichier de métriques
project_root = Path(__file__).parent.parent.parent
METRICS_FILE = project_root / "data" / "metrics" / "metrics.jsonl"
SUMMARY_FILE = project_root / "data" / "metrics" / "summary.json"

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

def get_recent_requests(limit: int = 10) -> List[Dict]:
    """Retourne les requêtes récentes formatées pour l'API."""
    requests = load_recent_requests(limit=limit)
    
    formatted = []
    for req in requests:
        formatted.append({
            "id": req.get("conversation_id", "unknown"),
            "timestamp": req.get("timestamp", ""),
            "user": "user@rag-system.io",  # TODO: Récupérer depuis le token JWT
            "question": req.get("query", "")[:50] + "..." if len(req.get("query", "")) > 50 else req.get("query", ""),
            "status": "success" if req.get("success", False) else "error",
            "latency": req.get("latencies", {}).get("end_to_end", 0.0)
        })
    
    return formatted

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