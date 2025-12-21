import os
import sys
import pickle
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from typing import List

# Ajouter le répertoire racine du projet au sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.Config import Config
import shutil

os.environ["USER_AGENT"] = "MyCustomUserAgent/1.0"

# Liste des URLs à scraper
urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://arxiv.org/pdf/2503.11651v1"
]

# Répertoire pour ChromaDB (chemin absolu basé sur le répertoire racine du projet)
CHROMA_DB_DIR = os.path.join(project_root, "data", "chroma_db")

# Cache pour les documents BM25
BM25_DOCS_CACHE = os.path.join(project_root, "data", "bm25_docs_cache.pkl")


def load_web_documents(urls: List[str]):
    """Charge les documents à partir d'URLs."""
    docs = [WebBaseLoader(url).load() for url in urls]
    return [item for sublist in docs for item in sublist]

def load_pdf_documents(pdf_paths: List[str]):
    """Charge les documents à partir de fichiers PDF."""
    docs = [PyPDFLoader(path).load() for path in pdf_paths]
    return [item for sublist in docs for item in sublist]

def split_documents(docs_list: List, chunk_size: int = 1000, chunk_overlap: int = 200):
    """Divise les documents en morceaux pour un traitement plus efficace."""
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return text_splitter.split_documents(docs_list)


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



def get_or_create_chroma_db(doc_splits: List, persist_directory: str = CHROMA_DB_DIR, clear_db: bool = False):
    """ 
    Vérifie si ChromaDB existe déjà et met à jour uniquement avec les nouveaux documents.
    Si clear_db est True, supprime complètement le dossier contenant la base et le recrée.
    """
    # Détection automatique du device
    device = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            print(f"[INFO] CUDA detecte pour ChromaDB: {torch.cuda.get_device_name(0)}")
        else:
            print("[INFO] CUDA non disponible pour ChromaDB, utilisation du CPU")
    except Exception:
        print("[INFO] Détection CUDA impossible, utilisation du CPU")
    
    embedding_model = NomicEmbeddings(
        model=Config.NomicEmbeddings_model, 
        inference_mode="local", 
        device=device
    )

    # 🔴 Si clear_db est True, on supprime totalement le dossier
    if clear_db:
        print(f"[INFO] Suppression complète de ChromaDB dans {persist_directory}...")
        shutil.rmtree(persist_directory)  # Supprime complètement le dossier ChromaDB
        print("[INFO] ChromaDB supprimée. Recréation en cours...")
        vectorstore = Chroma.from_documents(
            documents=doc_splits,
            embedding=embedding_model,
            persist_directory=persist_directory
        )

    else:
        # 💡 La base n'existe pas ou a été supprimée → Création
        print("[INFO] ChromaDB déjà existante. Chargement en cours...")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)
        print("[INFO] ChromaDB chargée.")

    return vectorstore


def load_pdf_documents_from_folder(folder_path: str):
    """Charge tous les fichiers PDF présents dans un dossier donné."""
    
    pdf_paths = [
        os.path.join(folder_path, file)
        for file in os.listdir(folder_path)
        if file.endswith(".pdf")
    ]

    return load_pdf_documents(pdf_paths)

def get_retriever(k: int = 3, use_hybrid: bool = None):
    """
    Crée un retriever pour récupérer les documents les plus pertinents.
    
    Args:
        k: Nombre de documents à retourner
        use_hybrid: Si True, utilise hybrid search (vector + BM25). 
                    Si None, utilise la config HYBRID_SEARCH_ENABLED
    """
    from langchain.retrievers import EnsembleRetriever
    from langchain_community.retrievers import BM25Retriever
    
    # Utiliser la config si use_hybrid n'est pas spécifié
    if use_hybrid is None:
        use_hybrid = getattr(Config, 'HYBRID_SEARCH_ENABLED', True)
    
    # Répertoire pour ChromaDB
    chroma_db_path = CHROMA_DB_DIR
    
    # Vérifier si ChromaDB existe déjà
    if os.path.exists(chroma_db_path) and os.listdir(chroma_db_path):
        # Si ChromaDB existe, juste charger le retriever sans recharger les documents
        print("[INFO] ChromaDB existe. Chargement du retriever uniquement...")
        
        # Détection intelligente du device
        device = "cpu"
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                print(f"[INFO] CUDA detecte: {torch.cuda.get_device_name(0)}")
            else:
                print("[INFO] CUDA non disponible, utilisation du CPU")
        except ImportError:
            print("[INFO] PyTorch non disponible, utilisation du CPU")
        except Exception as e:
            print(f"[INFO] Erreur detection CUDA: {str(e)}, utilisation du CPU")
        
        embedding_model = NomicEmbeddings(
            model=Config.NomicEmbeddings_model, 
            inference_mode="local", 
            device=device
        )
        vectorstore = Chroma(persist_directory=chroma_db_path, embedding_function=embedding_model)
        print(f"[INFO] Vectorstore charge depuis ChromaDB existante (device: {device}).")
        
        # Créer le retriever vectoriel
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        # Si hybrid search est activé, créer ensemble retriever
        if use_hybrid:
            print("[INFO] Activation du Hybrid Search (Vector + BM25)...")
            
            # Essayer d'abord de charger depuis le cache pickle
            bm25_documents = _load_bm25_documents()
            
            if bm25_documents:
                print("[INFO] Documents BM25 charges depuis le cache")
            else:
                # Fallback: essayer de charger depuis ChromaDB
                print("[INFO] Cache BM25 non trouve, tentative de chargement depuis ChromaDB...")
                try:
                    all_docs = vectorstore.get()
                    if all_docs and 'documents' in all_docs and len(all_docs['documents']) > 0:
                        # Créer des Document objects à partir des données ChromaDB
                        from langchain.schema import Document
                        bm25_documents = []
                        for i, doc_text in enumerate(all_docs['documents']):
                            metadata = all_docs.get('metadatas', [{}])[i] if 'metadatas' in all_docs else {}
                            bm25_documents.append(Document(page_content=doc_text, metadata=metadata))
                        print("[INFO] Documents BM25 charges depuis ChromaDB")
                    else:
                        raise ValueError("Pas de documents dans ChromaDB")
                except Exception as e:
                    print(f"[WARNING] Impossible de charger les documents pour BM25: {str(e)}")
                    print("[INFO] Utilisation du retriever vectoriel uniquement")
                    return vector_retriever
            
            # Créer le retriever BM25 avec les documents chargés
            try:
                bm25_retriever = BM25Retriever.from_documents(bm25_documents)
                bm25_retriever.k = k
                
                # Créer l'ensemble retriever avec poids
                vector_weight = getattr(Config, 'VECTOR_SEARCH_WEIGHT', 0.7)
                bm25_weight = getattr(Config, 'BM25_SEARCH_WEIGHT', 0.3)
                
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[vector_retriever, bm25_retriever],
                    weights=[vector_weight, bm25_weight]
                )
                
                print(f"[INFO] Hybrid Search configure (Vector: {vector_weight*100}%, BM25: {bm25_weight*100}%)")
                return ensemble_retriever
            except Exception as e:
                print(f"[WARNING] Erreur lors de la creation du retriever BM25: {str(e)}")
                print("[INFO] Utilisation du retriever vectoriel uniquement")
                return vector_retriever
        else:
            print("[INFO] Hybrid Search desactive, utilisation du retriever vectoriel uniquement")
            return vector_retriever
    
    # Si ChromaDB n'existe pas, charger et indexer les documents
    print("[INFO] ChromaDB n'existe pas. Chargement des documents...")
    print("[INFO] ⏳ Cette étape peut prendre plusieurs minutes la première fois...")
    
    # Charger les documents web
    print("[INFO] Chargement des documents web...")
    try:
        web_docs = load_web_documents(urls)
        print(f"[INFO] {len(web_docs)} documents web chargés.")
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement des documents web: {str(e)}")
        web_docs = []
    
    # Charger automatiquement tous les PDFs du dossier "data/raw"
    raw_data_folder = os.path.join(project_root, "data", "raw")
    pdf_docs = []
    if os.path.exists(raw_data_folder):
        try:
            pdf_docs = load_pdf_documents_from_folder(raw_data_folder)
            print(f"[INFO] {len(pdf_docs)} documents PDF chargés.")
        except Exception as e:
            print(f"⚠️ Erreur lors du chargement des PDFs: {str(e)}")
    else:
        print(f"[INFO] Dossier {raw_data_folder} n'existe pas. Aucun PDF chargé.")
    
    # Fusionner les deux listes de documents
    all_docs = web_docs + pdf_docs
    
    if not all_docs:
        raise Exception("Aucun document trouvé à indexer. Vérifiez vos sources de documents.")
    
    # Diviser les documents en segments
    print("[INFO] Segmentation des documents...")
    doc_splits = split_documents(all_docs)
    print(f"[INFO] {len(doc_splits)} chunks créés.")
    
    # Créer la base ChromaDB
    print("[INFO] Création de la base vectorielle ChromaDB...")
    vectorstore = get_or_create_chroma_db(doc_splits, CHROMA_DB_DIR, clear_db=False)
    print("[INFO] ChromaDB créée avec succès.")
    
    # Sauvegarder les documents pour BM25 cache
    _save_bm25_documents(doc_splits)
    
    # Créer le retriever vectoriel
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    
    # Si hybrid search est activé, créer ensemble retriever
    if use_hybrid:
        print("[INFO] Activation du Hybrid Search (Vector + BM25)...")
        try:
            # Créer le retriever BM25 avec les documents splits
            bm25_retriever = BM25Retriever.from_documents(doc_splits)
            bm25_retriever.k = k
            
            # Créer l'ensemble retriever avec poids
            vector_weight = getattr(Config, 'VECTOR_SEARCH_WEIGHT', 0.7)
            bm25_weight = getattr(Config, 'BM25_SEARCH_WEIGHT', 0.3)
            
            ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[vector_weight, bm25_weight]
            )
            
            print(f"[INFO] Hybrid Search configure (Vector: {vector_weight*100}%, BM25: {bm25_weight*100}%)")
            return ensemble_retriever
        except Exception as e:
            print(f"[WARNING] Erreur lors de la creation du retriever BM25: {str(e)}")
            print("[INFO] Utilisation du retriever vectoriel uniquement")
            return vector_retriever
    else:
        print("[INFO] Hybrid Search desactive, utilisation du retriever vectoriel uniquement")
        return vector_retriever


if __name__ == "__main__":
    retriever = get_retriever()
    #print(retriever.search("What is a transformer?"))