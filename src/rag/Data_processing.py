import os
import sys
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic.embeddings import NomicEmbeddings
from typing import List
rag_module_path = os.path.abspath("config")
sys.path.append(rag_module_path)
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

# Répertoire pour ChromaDB
CHROMA_DB_DIR = "data\chroma_db"


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
    embedding_model = NomicEmbeddings(
        model=Config.NomicEmbeddings_model, inference_mode="local", device="cuda"
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
    
    # Charger les documents web
    web_docs = load_web_documents(urls)

    # Charger automatiquement tous les PDFs du dossier "Dataset"
    pdf_docs = load_pdf_documents_from_folder("data\\raw")
    
    # Fusionner les deux listes de documents
    all_docs = web_docs + pdf_docs
    
    # Diviser les documents en segments
    doc_splits = split_documents(all_docs)
    
    # Vérifier/créer la base ChromaDB
    vectorstore = get_or_create_chroma_db(doc_splits, CHROMA_DB_DIR,False)
    
    # Retourner le retriever
    return vectorstore.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    retriever = get_retriever()
    #print(retriever.search("What is a transformer?"))