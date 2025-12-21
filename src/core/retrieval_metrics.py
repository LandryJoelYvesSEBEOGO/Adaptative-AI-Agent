"""
Module pour les métriques de retrieval (Precision, Recall, MAP)
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
import threading

# Lock pour thread-safety
_retrieval_metrics_lock = threading.Lock()


class RetrievalMetricsCollector:
    """Collecteur de métriques spécifiques au retrieval."""
    
    def __init__(self, metrics_file: Optional[Path] = None):
        if metrics_file is None:
            # Utiliser le même répertoire que les autres métriques
            metrics_dir = Path(__file__).parent.parent.parent / "data" / "metrics"
            metrics_dir.mkdir(parents=True, exist_ok=True)
            metrics_file = metrics_dir / "retrieval_results.jsonl"
        
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    def record_retrieval(
        self,
        conversation_id: str,
        query: str,
        retrieved_doc_ids: List[str],
        retrieved_sources: Optional[List[str]] = None
    ):
        """
        Enregistre les résultats d'une recherche retrieval.
        
        Args:
            conversation_id: ID unique de la conversation
            query: Question de l'utilisateur
            retrieved_doc_ids: Liste des IDs des documents récupérés (chunk_id ou parent_doc_id)
            retrieved_sources: Liste des sources des documents récupérés (optionnel)
        """
        timestamp = datetime.now().isoformat()
        
        entry = {
            "timestamp": timestamp,
            "conversation_id": conversation_id,
            "query": query[:500],  # Limiter la longueur
            "retrieved_doc_ids": retrieved_doc_ids,
            "retrieved_sources": retrieved_sources or [],
            "num_retrieved": len(retrieved_doc_ids)
        }
        
        with _retrieval_metrics_lock:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def load_retrieval_results(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Charge les résultats de retrieval enregistrés.
        
        Args:
            limit: Nombre maximum de résultats à charger (None = tous)
        
        Returns:
            Liste des résultats de retrieval
        """
        if not self.metrics_file.exists():
            return []
        
        results = []
        with open(self.metrics_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
                    
                    if limit and len(results) >= limit:
                        break
        
        return results


def calculate_precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calcule Precision@k.
    
    Args:
        retrieved_ids: Liste des IDs des documents récupérés (ordre important)
        relevant_ids: Set des IDs des documents pertinents (ground truth)
        k: Nombre de documents à considérer (k premiers)
    
    Returns:
        Precision@k (0.0 à 1.0)
    """
    if k == 0 or not retrieved_ids:
        return 0.0
    
    # Prendre les k premiers documents
    top_k_retrieved = retrieved_ids[:k]
    
    # Compter combien sont pertinents
    relevant_retrieved = sum(1 for doc_id in top_k_retrieved if doc_id in relevant_ids)
    
    return relevant_retrieved / min(k, len(top_k_retrieved))


def calculate_recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """
    Calcule Recall@k.
    
    Args:
        retrieved_ids: Liste des IDs des documents récupérés (ordre important)
        relevant_ids: Set des IDs des documents pertinents (ground truth)
        k: Nombre de documents à considérer (k premiers)
    
    Returns:
        Recall@k (0.0 à 1.0)
    """
    if not relevant_ids:
        return 0.0 if retrieved_ids else 1.0
    
    if k == 0 or not retrieved_ids:
        return 0.0
    
    # Prendre les k premiers documents
    top_k_retrieved = retrieved_ids[:k]
    
    # Compter combien de documents pertinents ont été récupérés
    relevant_retrieved = sum(1 for doc_id in top_k_retrieved if doc_id in relevant_ids)
    
    return relevant_retrieved / len(relevant_ids)


def calculate_average_precision(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """
    Calcule Average Precision (AP) pour une requête.
    
    Args:
        retrieved_ids: Liste des IDs des documents récupérés (ordre important)
        relevant_ids: Set des IDs des documents pertinents (ground truth)
    
    Returns:
        Average Precision (0.0 à 1.0)
    """
    if not relevant_ids:
        return 0.0
    
    if not retrieved_ids:
        return 0.0
    
    # Calculer la précision à chaque position où on trouve un document pertinent
    precisions = []
    relevant_count = 0
    
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            relevant_count += 1
            # Precision à la position i+1
            precision_at_i = relevant_count / (i + 1)
            precisions.append(precision_at_i)
    
    # Si aucun document pertinent n'a été récupéré
    if not precisions:
        return 0.0
    
    # Average Precision = moyenne des précisions
    return sum(precisions) / len(relevant_ids)


def calculate_mean_average_precision(
    retrieval_results: List[Dict],
    ground_truth: Dict[str, Set[str]]
) -> float:
    """
    Calcule Mean Average Precision (MAP) sur un ensemble de requêtes.
    
    Args:
        retrieval_results: Liste de dicts avec 'query' et 'retrieved_doc_ids'
        ground_truth: Dict {query: set of relevant doc ids}
    
    Returns:
        MAP (0.0 à 1.0)
    """
    if not retrieval_results:
        return 0.0
    
    average_precisions = []
    
    for result in retrieval_results:
        query = result.get('query', '').strip()
        retrieved_ids = result.get('retrieved_doc_ids', [])
        
        # Trouver les documents pertinents pour cette query
        relevant_ids = ground_truth.get(query, set())
        
        if relevant_ids:
            ap = calculate_average_precision(retrieved_ids, relevant_ids)
            average_precisions.append(ap)
    
    if not average_precisions:
        return 0.0
    
    return sum(average_precisions) / len(average_precisions)


def calculate_retrieval_metrics(
    retrieval_results: List[Dict],
    ground_truth: Dict[str, Set[str]],
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict:
    """
    Calcule toutes les métriques de retrieval sur un ensemble de résultats.
    
    Args:
        retrieval_results: Liste de dicts avec 'query' et 'retrieved_doc_ids'
        ground_truth: Dict {query: set of relevant doc ids}
        k_values: Liste des valeurs de k pour calculer Precision@k et Recall@k
    
    Returns:
        Dictionnaire avec toutes les métriques calculées
    """
    metrics = {
        "num_queries": len(retrieval_results),
        "precision_at_k": {},
        "recall_at_k": {},
        "mean_average_precision": 0.0
    }
    
    # Calculer Precision@k et Recall@k pour chaque k
    for k in k_values:
        precisions = []
        recalls = []
        
        for result in retrieval_results:
            query = result.get('query', '').strip()
            retrieved_ids = result.get('retrieved_doc_ids', [])
            relevant_ids = ground_truth.get(query, set())
            
            if relevant_ids:
                precision = calculate_precision_at_k(retrieved_ids, relevant_ids, k)
                recall = calculate_recall_at_k(retrieved_ids, relevant_ids, k)
                precisions.append(precision)
                recalls.append(recall)
        
        if precisions:
            metrics["precision_at_k"][f"P@{k}"] = sum(precisions) / len(precisions)
            metrics["recall_at_k"][f"R@{k}"] = sum(recalls) / len(recalls)
    
    # Calculer MAP
    metrics["mean_average_precision"] = calculate_mean_average_precision(
        retrieval_results, ground_truth
    )
    
    return metrics


# Instance globale
_retrieval_metrics_collector = None

def get_retrieval_metrics_collector() -> RetrievalMetricsCollector:
    """Récupère l'instance globale du collecteur de métriques de retrieval."""
    global _retrieval_metrics_collector
    if _retrieval_metrics_collector is None:
        from config.Config import Config
        metrics_file = getattr(Config, 'RETRIEVAL_METRICS_FILE', None)
        if metrics_file:
            metrics_file = Path(metrics_file)
        _retrieval_metrics_collector = RetrievalMetricsCollector(metrics_file)
    return _retrieval_metrics_collector