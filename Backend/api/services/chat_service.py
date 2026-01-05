import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import uuid
import time
import re

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.Rag_model import get_final_response, get_final_response_stream

def extract_citations(response_text: str) -> List[Dict]:
    """
    Extrait les citations de la réponse RAG.
    Format attendu: [1], [2], etc. dans le texte.
    """
    citations = []
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, response_text)
    
    # Pour l'instant, on retourne des citations génériques
    # Dans une implémentation complète, on récupérerait les vraies citations depuis le state RAG
    unique_ids = list(set(matches))
    for citation_id in unique_ids:
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