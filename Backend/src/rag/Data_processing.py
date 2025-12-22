import os
import sys
import pickle
import uuid
import json
from datetime import datetime
from langchain.schema import Document
import re
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
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
    doc_splits = text_splitter.split_documents(docs_list)
    
    # Enrichir les métadonnées
    enriched_splits = enrich_document_metadata(doc_splits)
    
    return enriched_splits


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

# LLM global pour l'extraction de métadonnées (singleton pattern)
_metadata_llm = None

def _get_metadata_llm():
    """Récupère ou crée le LLM pour l'extraction de métadonnées (lazy loading)."""
    global _metadata_llm
    if _metadata_llm is None:
        _metadata_llm = ChatGroq(
            model_name=Config.GROQ_model,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}},
            groq_api_key=Config.GROQ_API_KEY
        )
    return _metadata_llm

def _extract_advanced_metadata(doc: Document) -> dict:
    """
    Extrait des métadonnées avancées d'un document en utilisant le LLM.
    
    Args:
        doc: Document LangChain à analyser
    
    Returns:
        Dictionnaire avec entities, keywords, topics, summary
    """
    advanced_metadata = {}
    
    # Vérifier quelles extractions sont activées
    extract_entities = getattr(Config, 'METADATA_EXTRACT_ENTITIES', True)
    extract_keywords = getattr(Config, 'METADATA_EXTRACT_KEYWORDS', True)
    extract_topics = getattr(Config, 'METADATA_EXTRACT_TOPICS', True)
    extract_summary = getattr(Config, 'METADATA_EXTRACT_SUMMARY', True)
    
    # Si aucune extraction n'est activée, retourner vide
    if not any([extract_entities, extract_keywords, extract_topics, extract_summary]):
        return advanced_metadata
    
    try:
        # Limiter la longueur du texte pour éviter les limites de tokens
        content = doc.page_content[:3000]  # Limiter à 3000 caractères
        
        if not content.strip():
            return advanced_metadata
        
        # Préparer le prompt pour l'extraction
        max_keywords = getattr(Config, 'METADATA_MAX_KEYWORDS', 5)
        max_entities = getattr(Config, 'METADATA_MAX_ENTITIES', 10)
        max_topics = getattr(Config, 'METADATA_MAX_TOPICS', 3)
        summary_length = getattr(Config, 'METADATA_SUMMARY_MAX_LENGTH', 100)
        
        extraction_prompt = f"""Analyze the following text and extract metadata. Return a JSON object with:
"""
        
        if extract_keywords:
            extraction_prompt += f"- 'keywords': list of {max_keywords} most important keywords (max {max_keywords} items)\n"
        
        if extract_entities:
            extraction_prompt += f"- 'entities': list of named entities (persons, organizations, locations, etc., max {max_entities} items)\n"
        
        if extract_topics:
            extraction_prompt += f"- 'topics': list of {max_topics} main topics/subjects (max {max_topics} items)\n"
        
        if extract_summary:
            extraction_prompt += f"- 'summary': a brief summary in max {summary_length} words\n"
        
        extraction_prompt += f"""
Text to analyze:
{content}

Return only valid JSON, no additional text."""

        # Appeler le LLM (utilise le singleton)
        llm_json = _get_metadata_llm()
        response = llm_json.invoke([HumanMessage(content=extraction_prompt)])
        
        # Parser la réponse JSON
        if hasattr(response, 'content'):
            extracted_data = json.loads(response.content)
            
            if extract_keywords and 'keywords' in extracted_data:
                keywords = extracted_data['keywords']
                if isinstance(keywords, list):
                    advanced_metadata['keywords'] = keywords[:max_keywords]
            
            if extract_entities and 'entities' in extracted_data:
                entities = extracted_data['entities']
                if isinstance(entities, list):
                    advanced_metadata['entities'] = entities[:max_entities]
            
            if extract_topics and 'topics' in extracted_data:
                topics = extracted_data['topics']
                if isinstance(topics, list):
                    advanced_metadata['topics'] = topics[:max_topics]
            
            if extract_summary and 'summary' in extracted_data:
                summary = extracted_data['summary']
                if isinstance(summary, str):
                    advanced_metadata['summary'] = summary
        
    except json.JSONDecodeError as e:
        print(f"[WARNING] Erreur parsing JSON pour extraction métadonnées: {str(e)}")
    except Exception as e:
        print(f"[WARNING] Erreur lors de l'extraction de métadonnées avancées: {str(e)}")
        # En cas d'erreur, continuer sans ces métadonnées
    
    return advanced_metadata


def enrich_document_metadata(doc_splits: List[Document]) -> List[Document]:
    """
    Enrichit les métadonnées des documents avec des informations structurelles.
    
    Args:
        doc_splits: Liste de documents (chunks) à enrichir
    
    Returns:
        Liste de documents avec métadonnées enrichies
    """
    if not doc_splits:
        return doc_splits
    
    metadata_enabled = getattr(Config, 'METADATA_ENRICHMENT_ENABLED', True)
    if not metadata_enabled:
        print("[INFO] Enrichissement des métadonnées désactivé")
        return doc_splits
    
    print("[INFO] Enrichissement des métadonnées des documents...")
    
    # Grouper les chunks par document parent (basé sur source ou créer des groupes)
    # Pour l'instant, on groupe par 'source' dans les métadonnées
    parent_groups = {}
    for idx, doc in enumerate(doc_splits):
        source = doc.metadata.get('source', f'unknown_{idx}')
        if source not in parent_groups:
            parent_groups[source] = []
        parent_groups[source].append((idx, doc))
    
    # Générer un ID unique pour chaque document parent
    parent_ids = {}
    for source in parent_groups:
        parent_ids[source] = str(uuid.uuid4())
    
    # Enrichir chaque chunk
    enriched_docs = []
    processed_at = datetime.now().isoformat()
    
    for source, chunks in parent_groups.items():
        parent_doc_id = parent_ids[source]
        total_chunks = len(chunks)
        
        for chunk_index, (original_idx, doc) in enumerate(chunks):
             # Créer une copie des métadonnées existantes
            enriched_metadata = doc.metadata.copy() if doc.metadata else {}
            
            # Ajouter les métadonnées structurelles
            enriched_metadata['chunk_id'] = str(uuid.uuid4())
            enriched_metadata['parent_doc_id'] = parent_doc_id
            enriched_metadata['chunk_index'] = chunk_index
            enriched_metadata['total_chunks'] = total_chunks
            
            # Métadonnées techniques
            enriched_metadata['processed_at'] = processed_at
            if 'created_at' not in enriched_metadata:
                enriched_metadata['created_at'] = processed_at
            
            # Langue (détection simple pour l'instant)
            detect_language = getattr(Config, 'METADATA_DETECT_LANGUAGE', False)
            if detect_language:
                # TODO: Implémenter la détection de langue plus tard
                enriched_metadata['language'] = 'en'  # Par défaut
            else:
                enriched_metadata['language'] = 'en'  # Par défaut pour l'instant
            
            # Extraire les métadonnées avancées (entities, keywords, topics, summary)
            advanced_metadata = _extract_advanced_metadata(doc)
            enriched_metadata.update(advanced_metadata)
            
            # Créer un nouveau document avec les métadonnées enrichies
            enriched_doc = Document(
                page_content=doc.page_content,
                metadata=enriched_metadata
            )
            enriched_docs.append((original_idx, enriched_doc))
    
    # Réorganiser selon l'ordre original et retourner uniquement les documents
    enriched_docs.sort(key=lambda x: x[0])
    result = [doc for _, doc in enriched_docs]
    
    print(f"[INFO] ✅ {len(result)} documents enrichis avec métadonnées structurelles")
    print(f"[INFO]   - {len(parent_groups)} documents parents identifiés")
    
    return result

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