"""
Système de métriques basique pour le RAG.
Mesure latences, compteurs, et stocke les données.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import threading

# Répertoire pour stocker les métriques
METRICS_DIR = Path(__file__).parent.parent.parent / "data" / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# Fichier pour les métriques en temps réel
METRICS_FILE = METRICS_DIR / "metrics.jsonl"
METRICS_SUMMARY_FILE = METRICS_DIR / "summary.json"

# Lock pour thread-safety
_metrics_lock = threading.Lock()


class MetricsCollector:
    """Collecteur de métriques pour le système RAG."""
    
    def __init__(self):
        self.metrics_file = METRICS_FILE
        self.summary_file = METRICS_SUMMARY_FILE
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """S'assure que les fichiers de métriques existent."""
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.summary_file.exists():
            self._init_summary()
    
    def _init_summary(self):
        """Initialise le fichier de résumé."""
        initial_summary = {
            "total_requests": 0,
            "total_errors": 0,
            "latencies": {
                "end_to_end": [],
                "retrieval": [],
                "generation": [],
                "grading": [],
                "web_search": [],
                "answer_quality": []
            },
            "answer_quality_scores": [],
            "answer_quality_breakdown": {
                "relevance": [],
                "completeness": [],
                "conciseness": [],
                "accuracy": [],
                "coherence": []
            },
            "last_updated": datetime.now().isoformat()
        }
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(initial_summary, f, indent=2)
    
    def record_request(
        self,
        conversation_id: str,
        query: str,
        latencies: Dict[str, float],
        success: bool = True,
        error: Optional[str] = None,
        num_documents: Optional[int] = None,
        response_length: Optional[int] = None,
        answer_quality_score: Optional[float] = None,
        answer_quality_scores: Optional[Dict] = None
    ):
        """
        Enregistre une requête complète avec ses métriques.
        
        Args:
            conversation_id: ID unique de la conversation
            query: Question de l'utilisateur
            latencies: Dict avec les latences (end_to_end, retrieval, generation, etc.)
            success: Si la requête a réussi
            error: Message d'erreur si échec
            num_documents: Nombre de documents récupérés
            response_length: Longueur de la réponse générée
            answer_quality_score: Score global de qualité de réponse (0-1)
            answer_quality_scores: Dict avec les scores détaillés (relevance, completeness, etc.)
        """
        timestamp = datetime.now().isoformat()
        
        metric_entry = {
            "timestamp": timestamp,
            "conversation_id": conversation_id,
            "query": query[:200],  # Tronquer pour éviter fichiers trop gros
            "success": success,
            "error": error,
            "latencies": latencies,
            "num_documents": num_documents,
            "response_length": response_length,
            "answer_quality_score": answer_quality_score,
            "answer_quality_scores": answer_quality_scores
        }
        
        # Écrire dans le fichier JSONL (une ligne par requête)
        with _metrics_lock:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metric_entry, ensure_ascii=False) + '\n')
            
            # Mettre à jour le résumé
            self._update_summary(metric_entry, latencies)
    
    def _update_summary(self, entry: Dict, latencies: Dict[str, float]):
        """Met à jour le fichier de résumé."""
        try:
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._init_summary()
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        
        # Mettre à jour les compteurs
        summary["total_requests"] += 1
        if not entry.get("success", True):
            summary["total_errors"] += 1
        
        # Ajouter les latences (garder les 1000 dernières)
        for metric_name, latency_value in latencies.items():
            if metric_name in summary["latencies"]:
                summary["latencies"][metric_name].append(latency_value)
                # Garder seulement les 1000 dernières valeurs
                if len(summary["latencies"][metric_name]) > 1000:
                    summary["latencies"][metric_name] = summary["latencies"][metric_name][-1000:]
        
        # Ajouter les scores de qualité
        answer_quality_score = entry.get("answer_quality_score")
        if answer_quality_score is not None:
            if "answer_quality_scores" not in summary:
                summary["answer_quality_scores"] = []
            summary["answer_quality_scores"].append(answer_quality_score)
            if len(summary["answer_quality_scores"]) > 1000:
                summary["answer_quality_scores"] = summary["answer_quality_scores"][-1000:]
        
        # Ajouter les scores détaillés
        answer_quality_scores = entry.get("answer_quality_scores")
        if answer_quality_scores and isinstance(answer_quality_scores, dict):
            if "answer_quality_breakdown" not in summary:
                summary["answer_quality_breakdown"] = {
                    "relevance": [],
                    "completeness": [],
                    "conciseness": [],
                    "accuracy": [],
                    "coherence": []
                }
            for criterion in ["relevance", "completeness", "conciseness", "accuracy", "coherence"]:
                if criterion in answer_quality_scores:
                    score_value = answer_quality_scores[criterion]
                    if isinstance(score_value, (int, float)):
                        summary["answer_quality_breakdown"][criterion].append(float(score_value))
                        if len(summary["answer_quality_breakdown"][criterion]) > 1000:
                            summary["answer_quality_breakdown"][criterion] = summary["answer_quality_breakdown"][criterion][-1000:]
        
        summary["last_updated"] = datetime.now().isoformat()
        
        # Sauvegarder
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def get_summary(self) -> Dict:
        """Récupère le résumé des métriques."""
        try:
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._init_summary()
            return self.get_summary()
    
    def get_statistics(self) -> Dict:
        """Calcule les statistiques (moyenne, médiane, p95, p99) des latences."""
        summary = self.get_summary()
        stats = {}
        
        for metric_name, values in summary["latencies"].items():
            if not values:
                stats[metric_name] = {
                    "count": 0,
                    "mean": 0,
                    "median": 0,
                    "p95": 0,
                    "p99": 0,
                    "min": 0,
                    "max": 0
                }
                continue
            
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            stats[metric_name] = {
                "count": n,
                "mean": sum(sorted_values) / n,
                "median": sorted_values[n // 2],
                "p95": sorted_values[int(n * 0.95)] if n > 0 else 0,
                "p99": sorted_values[int(n * 0.99)] if n > 0 else 0,
                "min": min(sorted_values),
                "max": max(sorted_values)
            }
        
        # Statistiques pour les scores de qualité
        quality_stats = {}
        if summary.get("answer_quality_scores"):
            quality_values = summary["answer_quality_scores"]
            sorted_quality = sorted(quality_values)
            n_quality = len(sorted_quality)
            quality_stats["overall"] = {
                "count": n_quality,
                "mean": sum(sorted_quality) / n_quality if n_quality > 0 else 0,
                "median": sorted_quality[n_quality // 2] if n_quality > 0 else 0,
                "p95": sorted_quality[int(n_quality * 0.95)] if n_quality > 0 else 0,
                "p99": sorted_quality[int(n_quality * 0.99)] if n_quality > 0 else 0,
                "min": min(sorted_quality) if sorted_quality else 0,
                "max": max(sorted_quality) if sorted_quality else 0
            }
        
        # Statistiques pour chaque critère
        quality_breakdown_stats = {}
        for criterion, values in summary.get("answer_quality_breakdown", {}).items():
            if not values:
                quality_breakdown_stats[criterion] = {
                    "count": 0,
                    "mean": 0,
                    "median": 0
                }
                continue
            
            sorted_criterion = sorted(values)
            n_criterion = len(sorted_criterion)
            quality_breakdown_stats[criterion] = {
                "count": n_criterion,
                "mean": sum(sorted_criterion) / n_criterion if n_criterion > 0 else 0,
                "median": sorted_criterion[n_criterion // 2] if n_criterion > 0 else 0
            }
        
        return {
            "total_requests": summary["total_requests"],
            "total_errors": summary["total_errors"],
            "error_rate": summary["total_errors"] / summary["total_requests"] if summary["total_requests"] > 0 else 0,
            "latency_stats": stats,
            "answer_quality_stats": quality_stats,
            "answer_quality_breakdown": quality_breakdown_stats,
            "last_updated": summary["last_updated"]
        }


# Instance globale
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Récupère l'instance globale du collecteur de métriques."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector