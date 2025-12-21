import pickle
import os 

BM25_DOCS_CACHE = os.path.join(project_root, "data", "bm25_docs_cache.pkl")

def _save_bm25_documents(doc_splits):
    """Sauvegarde les documents pour BM25 dans un fichier cache."""
    try:
        os.makedirs(os.path.dirname(BM25_DOCS_CACHE), exist_ok=True)
        with open(BM25_DOCS_CACHE, 'wb') as f:
            pickle.dump(doc_splits, f)
        print("[INFO] Documents sauvegardes pour BM25 cache")
    except Exception as e:
        print(f"[WARNING] Impossible de sauvegarder BM25 cache: {str(e)}")

def _load_bm25_documents():
    """Charge les documents pour BM25 depuis le cache."""
    try:
        if os.path.exists(BM25_DOCS_CACHE):
            with open(BM25_DOCS_CACHE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"[WARNING] Impossible de charger BM25 cache: {str(e)}")
    return None