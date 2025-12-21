import os
import sys
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

def get_retriever(k: int = 3):
    """Crée un retriever pour récupérer les documents les plus pertinents."""
    
    # Répertoire pour ChromaDB
    chroma_db_path = CHROMA_DB_DIR
    
    # Vérifier si ChromaDB existe déjà
    if os.path.exists(chroma_db_path) and os.listdir(chroma_db_path):
        # Si ChromaDB existe, juste charger le retriever sans recharger les documents
        print("[INFO] ChromaDB existe. Chargement du retriever uniquement...")
        
        # Détection intelligente du device
        device = "cpu"  # Par défaut CPU
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                print(f"[INFO] CUDA detecte: {torch.cuda.get_device_name(0)}")
            else:
                print("[INFO] CUDA non disponible, utilisation du CPU")
                print("[INFO] Pour utiliser GPU, installez PyTorch avec CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        except ImportError:
            print("[INFO] PyTorch non disponible, utilisation du CPU")
        except Exception as e:
            print(f"[INFO] Erreur detection CUDA: {str(e)}, utilisation du CPU")
        
        embedding_model = NomicEmbeddings(
            model=Config.NomicEmbeddings_model, 
            inference_mode="local", 
            device=device  # Détection automatique
        )
        vectorstore = Chroma(persist_directory=chroma_db_path, embedding_function=embedding_model)
        print(f"[INFO] Retriever charge depuis ChromaDB existante (device: {device}).")
        return vectorstore.as_retriever(search_kwargs={"k": k})
    
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
    
    # Retourner le retriever
    return vectorstore.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    retriever = get_retriever()
    #print(retriever.search("What is a transformer?"))