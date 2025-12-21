# Import necessary libraries
import os 
import sys
import time
import re
from typing import Tuple
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langgraph.graph import StateGraph, END
from IPython.display import Image, display
from langchain.schema import Document
from typing import List, Annotated, Dict, Optional, Callable
from typing_extensions import TypedDict
from sentence_transformers import CrossEncoder
import json
import operator

# Ajouter le répertoire racine du projet au sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.Config import Config
from src.rag.Prompts import get_prompts
from src.rag.Data_processing import get_retriever
from src.core.exceptions import (
    RetrievalException, LLMAPIException, LLMTimeoutException,
    LLMQuotaException, InvalidResponseException, MaxRetriesException,
    WebSearchException, HallucinationDetectedException, ValidationException
)
import uuid
from src.core.metrics import get_metrics_collector
from src.core.retrieval_metrics import get_retrieval_metrics_collector
from src.core.logger import get_logger

# Initialiser logger et metrics
logger = get_logger()
metrics = get_metrics_collector()
# Load environment variables
load_dotenv()

# Initialize the necessary components
local_llm = ChatGroq(
    model_name=Config.GROQ_model,
    temperature=0,
    groq_api_key=Config.GROQ_API_KEY
)

llm_json_mode = ChatGroq(
    model_name=Config.GROQ_model, 
    temperature=0,
    model_kwargs={"response_format": {"type": "json_object"}},
    groq_api_key=Config.GROQ_API_KEY
)

# Dans Rag_model.py, remplacez la ligne 48:
# retriever = get_retriever()

# Par une initialisation lazy:
_retriever = None

def get_retriever_instance():
    """Récupère ou crée le retriever (lazy loading pour éviter blocage à l'import)."""
    global _retriever
    if _retriever is None:
        print("[INIT] ⏳ Initialisation du retriever (première fois, peut prendre du temps)...")
        try:
            # Si reranker activé, récupérer plus de documents pour le reranking
            reranker_enabled = getattr(Config, 'RERANKER_ENABLED', True)
            if reranker_enabled:
                reranker_top_k = getattr(Config, 'RERANKER_TOP_K', 20)
                _retriever = get_retriever(k=reranker_top_k)
                print(f"[INIT] ✅ Retriever créé avec k={reranker_top_k} (pour reranking).")
            else:
                final_k = getattr(Config, 'RERANKER_FINAL_K', 3)
                _retriever = get_retriever(k=final_k)
                print(f"[INIT] ✅ Retriever créé avec k={final_k}.")
            
            # IMPORTANT: Précharger le modèle d'embedding pour éviter le blocage au premier appel
            # Cela force le chargement du modèle en mémoire maintenant plutôt que lors du premier invoke
            print("[INIT] ⏳ Préchargement du modèle d'embedding (peut prendre 10-30s)...")
            try:
                start_preload = time.time()
                # Faire un appel test pour précharger le modèle
                test_docs = _retriever.invoke("test preload")
                preload_time = time.time() - start_preload
                print(f"[INIT] ✅ Modèle préchargé avec succès en {preload_time:.2f}s")
                print("[INIT] Le retriever est maintenant prêt à être utilisé sans blocage.")
            except Exception as preload_error:
                print(f"⚠️ [INIT] Attention: Échec du préchargement: {str(preload_error)}")
                print("[INIT] Le retriever sera initialisé lors du premier appel réel.")
                # On continue quand même, le retriever sera initialisé au premier appel
                
        except Exception as e:
            print(f"❌ [INIT] Erreur lors de l'initialisation du retriever: {str(e)}")
            raise
    return _retriever

web_search_tool = TavilySearchResults(k=3, tavily_api_key=Config.TAVILY_API_KEY)

# Load prompts
prompt = get_prompts()

# Fonction helper pour retry avec backoff
def retry_with_backoff(func: Callable, max_retries: int = None, 
                      initial_delay: int = None) -> any:
    """Retry une fonction avec backoff exponentiel."""
    if max_retries is None:
        max_retries = getattr(Config, 'MAX_RETRIES', 3)
    if initial_delay is None:
        initial_delay = getattr(Config, 'RETRY_INITIAL_DELAY', 1)
    
    backoff_factor = getattr(Config, 'RETRY_BACKOFF_FACTOR', 2)
    
    for attempt in range(max_retries):
        try:
            return func()
        except (LLMTimeoutException, LLMQuotaException, Exception) as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (backoff_factor ** attempt)
            print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée. Retry dans {delay}s...")
            time.sleep(delay)
    raise MaxRetriesException(f"Échec après {max_retries} tentatives")


def Rewrite_query(query: str) -> str:
    """Rewrite the query to be more specific."""
    try:
        print("---Rewrite the query---")
        if not query or not query.strip():
            return query
        
        rewritting_prompt_formatted = prompt["Rewritting_prompt"].format(query=query)
        
        def _call_llm():
            return local_llm.invoke([HumanMessage(content=rewritting_prompt_formatted)])
        
        generation = retry_with_backoff(_call_llm)
        
        if hasattr(generation, "content"):
            return generation.content
        elif isinstance(generation, str):
            return generation
        else:
            raise InvalidResponseException(
                "Format de réponse invalide lors de la réécriture de la requête",
                {"query": query, "response_type": type(generation).__name__}
            )
    except Exception as e:
        # En cas d'erreur, retourner la query originale
        print(f"⚠️ Erreur lors de la réécriture: {str(e)}. Utilisation de la requête originale.")
        return query


# Post-processing function for formatting documents
def format_docs(docs, with_citations: bool = True):
    """
    Format documents for display with optional citation numbers.
    
    Args:
        docs: Liste de documents
        with_citations: Si True, ajoute des numéros de référence [1], [2], etc.
    
    Returns:
        String formatée avec les documents
    """
    if not docs:
        return ""
    
    if not with_citations:
        return "\n\n".join(doc.page_content for doc in docs if hasattr(doc, 'page_content'))
    
    formatted_parts = []
    for idx, doc in enumerate(docs, start=1):
        if hasattr(doc, 'page_content'):
            content = f"[Document {idx}]\n{doc.page_content}"
            formatted_parts.append(content)
    
    return "\n\n".join(formatted_parts)



def extract_sources_from_documents(documents: List[Document]) -> List[Dict[str, str]]:
    """
    Extrait les informations de source de chaque document.
    
    Args:
        documents: Liste de documents LangChain
    
    Returns:
        Liste de dictionnaires avec les infos de source
    """
    sources = []
    for idx, doc in enumerate(documents, start=1):
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        source_info = {
            "number": idx,
            "source": metadata.get('source', 'Unknown source'),
            "parent_doc_id": metadata.get('parent_doc_id', ''),
            "chunk_id": metadata.get('chunk_id', ''),
            "title": metadata.get('title', '') or metadata.get('source', '').split('/')[-1]
        }
        sources.append(source_info)
    return sources


def format_citations(response: str, sources: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Parse les citations dans la réponse et formate les références.
    
    Args:
        response: Réponse générée avec citations [1], [2], etc.
        sources: Liste des sources extraites des documents
    
    Returns:
        Tuple (response_with_citations, references_section)
    """
    if not sources:
        return response, ""
    
    # Extraire les numéros de citations utilisés (ex: [1], [2], [12])
    citation_pattern = r'\[(\d+)\]'
    citations_used = set()
    
    def replace_citation(match):
        num = int(match.group(1))
        if 1 <= num <= len(sources):
            citations_used.add(num)
            return f'[{num}]'
        return match.group(0)
    
    # Remplacer les citations par des références formatées
    response_formatted = re.sub(citation_pattern, replace_citation, response)
    
    # Créer la section des références
    if citations_used:
        references_parts = ["\n\n**Références:**"]
        for num in sorted(citations_used):
            source_info = sources[num - 1]  # -1 car les indices commencent à 0
            source_display = source_info.get('title') or source_info.get('source', f'Document {num}')
            references_parts.append(f"[{num}] {source_display}")
        
        references_section = "\n".join(references_parts)
    else:
        references_section = ""
    
    return response_formatted, references_section


# GraphState definition
class GraphState(TypedDict):
    question: str
    generation: str
    web_search: str
    max_retries: int
    answers: int
    loop_step: Annotated[int, operator.add]
    documents: List[str]
    error_history: List[str]  # Nouveau : historique des erreurs
    conversation_id: Optional[str]  # ID de conversation pour métriques
    latencies: Optional[Dict[str, float]]  # Latences pour métriques

# Reranker global (lazy loading)
_reranker = None

def get_reranker_instance():
    """Récupère ou crée le reranker cross-encoder (lazy loading)."""
    global _reranker
    if _reranker is None:
        reranker_enabled = getattr(Config, 'RERANKER_ENABLED', True)
        if not reranker_enabled:
            return None
        
        reranker_model = getattr(Config, 'RERANKER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
        print(f"[RERANKER] ⏳ Initialisation du reranker: {reranker_model}...")
        try:
            _reranker = CrossEncoder(reranker_model)
            print("[RERANKER] ✅ Reranker initialisé avec succès")
        except Exception as e:
            print(f"[RERANKER] ❌ Erreur lors de l'initialisation: {str(e)}")
            print("[RERANKER] Le reranking sera désactivé pour cette session")
            return None
    return _reranker

def rerank_documents(query: str, documents: List[Document], top_k: int = None) -> List[Document]:
    """
    Rerank les documents avec un cross-encoder.
    
    Args:
        query: La question de l'utilisateur
        documents: Liste de documents à reranker
        top_k: Nombre de documents à retourner après reranking
    
    Returns:
        Liste de documents rerankés (top_k premiers)
    """
    if not documents or len(documents) == 0:
        return documents
    
    reranker = get_reranker_instance()
    if reranker is None:
        # Si reranker non disponible, retourner les documents originaux
        return documents[:top_k] if top_k else documents
    
    if top_k is None:
        top_k = getattr(Config, 'RERANKER_FINAL_K', 3)
    
    try:
        # Préparer les paires (query, document) pour le cross-encoder
        pairs = [[query, doc.page_content] for doc in documents]
        
        # Calculer les scores de pertinence
        scores = reranker.predict(pairs)
        
        # Créer une liste de tuples (score, document) et trier par score décroissant
        scored_docs = list(zip(scores, documents))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Retourner les top_k documents
        reranked_docs = [doc for _, doc in scored_docs[:top_k]]
        
        return reranked_docs
        
    except Exception as e:
        print(f"[RERANKER] ⚠️ Erreur lors du reranking: {str(e)}")
        print("[RERANKER] Retour des documents originaux (sans reranking)")
        return documents[:top_k] if top_k else documents

        
# Node functions
def retrieve(state: Dict) -> Dict:
    """Retrieve documents from the vector store."""
    start_time = time.time()
    conversation_id = state.get("conversation_id", "unknown")
    latencies = state.get("latencies", {})
    
    try:
        logger.info("Retrieval started", extra={"component": "retrieval", "conversation_id": conversation_id})
        print("---RETRIEVE---")
        if not state.get("question"):
            raise RetrievalException("Question manquante pour la récupération")
        
        print(f"[RETRIEVE] Recherche de documents pour: {state['question'][:50]}...")
        
        # Obtenir le retriever (lazy loading)
        print("[RETRIEVE] Obtention du retriever...")
        current_retriever = get_retriever_instance()
        print("[RETRIEVE] ✅ Retriever obtenu.")
        
        print("[RETRIEVE] Appel retriever.invoke()...")
        print("[RETRIEVE] Cette etape va:")
        print("[RETRIEVE]   1. Generer l'embedding de la question")
        print("[RETRIEVE]   2. Rechercher dans ChromaDB")
        print("[RETRIEVE] ⏳ Veuillez patienter...")
        
        # IMPORTANT: LangGraph exécute les nœuds directement, sans threading supplémentaire
        # Le threading peut causer des conflits avec le runtime de LangGraph
        # Appel direct: si ça bloque, c'est que le problème vient de NomicEmbeddings/ChromaDB
        try:
            # Déterminer les paramètres du reranker
            reranker_enabled = getattr(Config, 'RERANKER_ENABLED', True)
            final_k = getattr(Config, 'RERANKER_FINAL_K', 3)
            
            # Le retriever a déjà été configuré avec le bon k dans get_retriever_instance
            print("[RETRIEVE] ⏳ Début de retriever.invoke()...")
            documents = current_retriever.invoke(state["question"])
            
            # Appliquer le reranking si activé
            if reranker_enabled and len(documents) > 1:
                print(f"[RETRIEVE] ⏳ Reranking de {len(documents)} documents (top-{final_k})...")
                rerank_start = time.time()
                documents = rerank_documents(state["question"], documents, top_k=final_k)
                rerank_time = time.time() - rerank_start
                latencies["reranking"] = rerank_time
                print(f"[RETRIEVE] ✅ Reranking terminé en {rerank_time:.3f}s ({len(documents)} documents finaux)")
            elif not reranker_enabled:
                # Si reranker désactivé, prendre les k premiers
                documents = documents[:final_k]
            
            elapsed_time = time.time() - start_time
            latencies["retrieval"] = elapsed_time
            print(f"[RETRIEVE] ✅ retriever.invoke() terminé avec succès en {elapsed_time:.2f}s")
        except Exception as e:
            elapsed_time = time.time() - start_time
            latencies["retrieval"] = elapsed_time
            print(f"[RETRIEVE] ❌ Exception apres {elapsed_time:.2f}s: {type(e).__name__}: {str(e)}")
            import traceback
            print("[RETRIEVE] Stack trace complete:")
            traceback.print_exc()
            raise RetrievalException(f"Erreur lors de l'invocation du retriever: {str(e)}") from e
        
        if documents is None:
            print("❌ [RETRIEVE] Aucun resultat retourne (None)")
            raise RetrievalException("Aucun resultat retourne par le retriever")
        
        if not documents or len(documents) == 0:
            print("⚠️ [RETRIEVE] Aucun document trouve")
            logger.warning(
                "No documents found",
                extra={"component": "retrieval", "conversation_id": conversation_id}
            )
            return {
                "documents": [],
                "error_history": state.get("error_history", []) + ["Aucun document trouve"],
                "latencies": latencies
            }
        
        print(f"[RETRIEVE] ✅ {len(documents)} documents trouves en {elapsed_time:.2f}s.")
        
        # Enregistrer les résultats de retrieval pour les métriques
        retrieval_metrics_enabled = getattr(Config, 'RETRIEVAL_METRICS_ENABLED', True)
        if retrieval_metrics_enabled:
            try:
                retrieval_collector = get_retrieval_metrics_collector()
                # Extraire les IDs des documents récupérés
                retrieved_doc_ids = []
                retrieved_sources = []
                for doc in documents:
                    # Utiliser parent_doc_id si disponible, sinon chunk_id, sinon source
                    doc_id = doc.metadata.get('parent_doc_id') or doc.metadata.get('chunk_id') or doc.metadata.get('source', 'unknown')
                    retrieved_doc_ids.append(str(doc_id))
                    source = doc.metadata.get('source', 'unknown')
                    retrieved_sources.append(str(source))
                
                retrieval_collector.record_retrieval(
                    conversation_id=conversation_id,
                    query=state["question"],
                    retrieved_doc_ids=retrieved_doc_ids,
                    retrieved_sources=retrieved_sources
                )
            except Exception as e:
                # Ne pas faire échouer le retrieval si l'enregistrement échoue
                print(f"[WARNING] Erreur lors de l'enregistrement des métriques retrieval: {str(e)}")
        
        logger.info(
            "Retrieval completed",
            extra={
                "component": "retrieval",
                "conversation_id": conversation_id,
                "data": {"latency": elapsed_time, "num_documents": len(documents)}
            }
        )
        return {"documents": documents, "latencies": latencies}
        
    except RetrievalException:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        latencies["retrieval"] = elapsed_time
        print(f"❌ [RETRIEVE] Exception non capturee: {str(e)}")
        logger.error(
            "Retrieval failed",
            extra={"component": "retrieval", "conversation_id": conversation_id},
            exc_info=True
        )
        import traceback
        traceback.print_exc()
        raise RetrievalException(f"Erreur recuperation: {str(e)}") from e


def generate(state: Dict) -> Dict:
    """Generate an answer using RAG on the retrieved documents."""
    start_time = time.time()
    conversation_id = state.get("conversation_id", "unknown")
    latencies = state.get("latencies", {})
    
    try:
        logger.info("Generation started", extra={"component": "generation", "conversation_id": conversation_id})
        print("---GENERATE---")
        
        if not state.get("documents"):
            raise GenerationException("Aucun document disponible pour la génération")
        
        # Vérifier si les citations sont activées
        citations_enabled = getattr(Config, 'CITATIONS_ENABLED', True)
        
        # Formater les documents (avec ou sans numéros de citation)
        docs_txt = format_docs(state["documents"], with_citations=citations_enabled)
        rag_prompt_formatted = prompt["rag_prompt"].format(
            context=docs_txt, 
            question=state["question"]
        )
        
        def _generate():
            return local_llm.invoke([HumanMessage(content=rag_prompt_formatted)])
        
        generation = retry_with_backoff(_generate)
        
        if not generation:
            raise InvalidResponseException("Réponse vide du LLM")
        
        # Extraire le contenu de la réponse
        generation_content = generation.content if hasattr(generation, 'content') else str(generation)
        
        # Traiter les citations si activées
        if citations_enabled:
            sources = extract_sources_from_documents(state["documents"])
            generation_content, references = format_citations(generation_content, sources)
            
            # Ajouter les références à la réponse si elles existent
            if references:
                generation_content = generation_content + references
        
        elapsed_time = time.time() - start_time
        latencies["generation"] = elapsed_time
        
        logger.info(
            "Generation completed",
            extra={
                "component": "generation",
                "conversation_id": conversation_id,
                "data": {"latency": elapsed_time, "citations_enabled": citations_enabled}
            }
        )
        
        return {
            "generation": generation_content,
            "loop_step": state.get("loop_step", 0) + 1,
            "latencies": latencies
        }
    except LLMQuotaException as e:
        elapsed_time = time.time() - start_time
        latencies["generation"] = elapsed_time
        raise LLMQuotaException(
            "Quota API dépassé. Veuillez réessayer plus tard.",
            {"loop_step": state.get("loop_step", 0)}
        ) from e
    except Exception as e:
        elapsed_time = time.time() - start_time
        latencies["generation"] = elapsed_time
        error_msg = f"Erreur lors de la génération: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(
            "Generation failed",
            extra={"component": "generation", "conversation_id": conversation_id},
            exc_info=True
        )
        from src.core.exceptions import GenerationException
        raise GenerationException(error_msg) from e


def grade_documents(state: Dict) -> Dict:
    """Grade the relevance of retrieved documents using multi-criteria evaluation."""
    start_time = time.time()
    conversation_id = state.get("conversation_id", "unknown")
    latencies = state.get("latencies", {})
    
    try:
        logger.info("Document grading started", extra={"component": "grading", "conversation_id": conversation_id})
        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        filtered_docs = []
        web_search = "No"
        
        if not state.get("documents"):
            elapsed_time = time.time() - start_time
            latencies["grading"] = elapsed_time
            return {"documents": [], "web_search": "Yes", "latencies": latencies}
        
        # Vérifier si multi-criteria grading est activé
        multi_criteria_enabled = getattr(Config, 'MULTI_CRITERIA_GRADING_ENABLED', True)
        
        all_scores = []  # Pour seuil adaptatif
        
        for doc in state["documents"]:
            try:
                multi_criteria_failed = False                
                if multi_criteria_enabled:
                    # Grading multi-critères
                    grader_prompt_formatted = prompt["multi_criteria_grader_prompt"].format(
                        document=doc.page_content[:4000],  # Limiter la longueur pour éviter token limit
                        question=state["question"]
                    )
                    
                    def _grade():
                        return llm_json_mode.invoke(
                            [SystemMessage(content=prompt["multi_criteria_grader_instructions"])] +
                            [HumanMessage(content=grader_prompt_formatted)]
                        )
                    
                    result = retry_with_backoff(_grade)
                    
                    try:
                        grade_data = json.loads(result.content)
                        
                        # Extraire les scores
                        scores = grade_data.get("scores", {})
                        relevance = float(scores.get("relevance", 0.0))
                        coverage = float(scores.get("coverage", 0.0))
                        freshness = float(scores.get("freshness", 0.7))  # Default si inconnu
                        authority = float(scores.get("authority", 0.7))  # Default si inconnu
                        clarity = float(scores.get("clarity", 0.7))
                        
                        # Calculer le score pondéré
                        weights = {
                            "relevance": getattr(Config, 'GRADING_RELEVANCE_WEIGHT', 0.35),
                            "coverage": getattr(Config, 'GRADING_COVERAGE_WEIGHT', 0.25),
                            "freshness": getattr(Config, 'GRADING_FRESHNESS_WEIGHT', 0.15),
                            "authority": getattr(Config, 'GRADING_AUTHORITY_WEIGHT', 0.15),
                            "clarity": getattr(Config, 'GRADING_CLARITY_WEIGHT', 0.10)
                        }
                        
                        overall_score = (
                            relevance * weights["relevance"] +
                            coverage * weights["coverage"] +
                            freshness * weights["freshness"] +
                            authority * weights["authority"] +
                            clarity * weights["clarity"]
                        )
                        
                        # Utiliser le score du LLM si fourni, sinon utiliser notre calcul
                        overall_score = float(grade_data.get("overall_score", overall_score))
                        all_scores.append(overall_score)
                        
                        # Déterminer le seuil
                        acceptance_threshold = getattr(Config, 'GRADING_ACCEPTANCE_THRESHOLD', 0.6)
                        adaptive_threshold = getattr(Config, 'GRADING_ADAPTIVE_THRESHOLD', True)
                        
                        if adaptive_threshold and len(all_scores) > 1:
                            # Seuil adaptatif : moyenne des scores * 0.8 (plus permissif)
                            threshold = (sum(all_scores) / len(all_scores)) * 0.8
                            threshold = max(threshold, acceptance_threshold * 0.7)  # Minimum 70% du seuil fixe
                        else:
                            threshold = acceptance_threshold
                        
                        accepted = grade_data.get("accepted", overall_score >= threshold)
                        reasoning = grade_data.get("reasoning", "")
                        
                        print(f"---GRADE: Score={overall_score:.2f} (R:{relevance:.2f}, C:{coverage:.2f}, F:{freshness:.2f}, A:{authority:.2f}, Cl:{clarity:.2f}) | Threshold={threshold:.2f}---")
                        if reasoning:
                            print(f"  Reasoning: {reasoning[:150]}...")
                        
                        if accepted and overall_score >= threshold:
                            print(f"✅ DOCUMENT ACCEPTED (score: {overall_score:.2f})")
                            filtered_docs.append(doc)
                        else:
                            print(f"❌ DOCUMENT REJECTED (score: {overall_score:.2f} < threshold: {threshold:.2f})")
                            web_search = "Yes"
                            
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        print(f"⚠️ Erreur parsing JSON multi-criteria: {str(e)}. Fallback sur grading binaire pour ce document.")
                        multi_criteria_failed = True
                    
                if not multi_criteria_enabled or multi_criteria_failed:
                    # Grading binaire (fallback ou désactivé)
                    doc_grader_prompt_formatted = prompt["doc_grader_prompt"].format(
                        document=doc.page_content[:4000],
                        question=state["question"]
                    )
                    
                    def _grade():
                        return llm_json_mode.invoke(
                            [SystemMessage(content=prompt["doc_grader_instructions"])] +
                            [HumanMessage(content=doc_grader_prompt_formatted)]
                        )
                    
                    result = retry_with_backoff(_grade)
                    
                    try:
                        grade_data = json.loads(result.content)
                        grade = grade_data.get("binary_score", "no")
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Erreur parsing JSON: {str(e)}. Score par défaut: no")
                        grade = "no"
                    
                    if grade.lower() == "yes":
                        print("---GRADE: DOCUMENT RELEVANT---")
                        filtered_docs.append(doc)
                    else:
                        print("---GRADE: DOCUMENT NOT RELEVANT---")
                        web_search = "Yes"
                        
            except Exception as e:
                print(f"⚠️ Erreur lors du grading d'un document: {str(e)}. Document ignoré.")
                web_search = "Yes"
                continue
        
        elapsed_time = time.time() - start_time
        latencies["grading"] = elapsed_time
        
        logger.info(
            "Document grading completed",
            extra={
                "component": "grading",
                "conversation_id": conversation_id,
                "data": {
                    "latency": elapsed_time,
                    "num_filtered": len(filtered_docs),
                    "num_total": len(state.get("documents", [])),
                    "multi_criteria": multi_criteria_enabled,
                    "avg_score": sum(all_scores) / len(all_scores) if all_scores else 0.0
                }
            }
        )
        
        return {"documents": filtered_docs, "web_search": web_search, "latencies": latencies}
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        latencies["grading"] = elapsed_time
        print(f"❌ Erreur dans grade_documents: {str(e)}")
        logger.error(
            "Document grading failed",
            extra={"component": "grading", "conversation_id": conversation_id},
            exc_info=True
        )
        # En cas d'erreur, on continue avec tous les documents
        return {"documents": state.get("documents", []), "web_search": "Yes", "latencies": latencies}

def web_search(state: Dict) -> Dict:
    """Perform a web search based on the question."""
    start_time = time.time()
    conversation_id = state.get("conversation_id", "unknown")
    latencies = state.get("latencies", {})
    
    try:
        logger.info("Web search started", extra={"component": "web_search", "conversation_id": conversation_id})
        print("---WEB SEARCH---")
        
        if not state.get("question"):
            raise WebSearchException("Question manquante pour la recherche web")
        
        def _search():
            return web_search_tool.invoke({"query": state["question"]})
        
        docs = retry_with_backoff(_search, max_retries=2)
        
        if not docs:
            print("⚠️ Aucun résultat de recherche web")
            elapsed_time = time.time() - start_time
            latencies["web_search"] = elapsed_time
            return {"documents": state.get("documents", []), "latencies": latencies}
        
        web_results = "\n".join([d.get("content", "") for d in docs if d.get("content")])
        
        if not web_results:
            print("⚠️ Résultats web vides")
            elapsed_time = time.time() - start_time
            latencies["web_search"] = elapsed_time
            return {"documents": state.get("documents", []), "latencies": latencies}
        
        documents = state.get("documents", [])
        documents.append(Document(page_content=web_results))
        
        elapsed_time = time.time() - start_time
        latencies["web_search"] = elapsed_time
        
        logger.info(
            "Web search completed",
            extra={
                "component": "web_search",
                "conversation_id": conversation_id,
                "data": {"latency": elapsed_time}
            }
        )
        
        return {"documents": documents, "latencies": latencies}
    except Exception as e:
        elapsed_time = time.time() - start_time
        latencies["web_search"] = elapsed_time
        error_msg = f"Erreur lors de la recherche web: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(
            "Web search failed",
            extra={"component": "web_search", "conversation_id": conversation_id},
            exc_info=True
        )
        # Ne pas bloquer, continuer avec les documents existants
        return {"documents": state.get("documents", []), "latencies": latencies}


# Edge functions
def route_question(state: Dict) -> str:
    """Route the question to either web search or RAG based on LLM decision."""
    try:
        print("---ROUTE QUESTION---")
        
        def _route():
            return llm_json_mode.invoke(
                [SystemMessage(content=prompt["router_instructions"])] +
                [HumanMessage(content=state["question"])]
            )
        
        route_result = retry_with_backoff(_route)
        
        try:
            route_data = json.loads(route_result.content)
            source = route_data.get("datasource", "vectorstore")
        except json.JSONDecodeError:
            print("⚠️ Erreur parsing JSON routing. Défaut: vectorstore")
            source = "vectorstore"
        
        return "websearch" if source == "websearch" else "vectorstore"
    except Exception as e:
        print(f"⚠️ Erreur lors du routing: {str(e)}. Défaut: vectorstore")
        return "vectorstore"  # Fallback sur vectorstore


def decide_to_generate(state: Dict) -> str:
    """Decide whether to generate an answer or add web search."""
    print("---ASSESS GRADED DOCUMENTS---")
    if state.get("web_search") == "Yes":
        print("---DECISION: INCLUDE WEB SEARCH---")
        return "websearch"
    else:
        print("---DECISION: GENERATE---")
        return "generate"


def grade_generation_v_documents_and_question(state: Dict) -> str:
    """Grade whether the generation is grounded in the document and answers the question."""
    try:
        print("---CHECK HALLUCINATIONS---")
        
        max_retries = state.get("max_retries", getattr(Config, 'MAX_RETRIES', 3))
        loop_step = state.get("loop_step", 0)
        
        if not state.get("generation"):
            raise ValidationException("Génération manquante pour la validation")
        
        generation_content = state["generation"].content if hasattr(state["generation"], "content") else str(state["generation"])
        
        # Vérification des hallucinations
        try:
            hallucination_grader_prompt_formatted = prompt["hallucination_grader_prompt"].format(
                documents=format_docs(state.get("documents", []), with_citations=False),
                generation=generation_content
            )
            
            def _check_hallucination():
                return llm_json_mode.invoke(
                    [SystemMessage(content=prompt["hallucination_grader_instructions"])] +
                    [HumanMessage(content=hallucination_grader_prompt_formatted)]
                )
            
            result = retry_with_backoff(_check_hallucination)
            
            try:
                grade_data = json.loads(result.content)
                grade = grade_data.get("binary_score", "no")
            except json.JSONDecodeError:
                print("⚠️ Erreur parsing JSON hallucination. Par défaut: no")
                grade = "no"
            
            if grade != "yes":
                if loop_step < max_retries:
                    print(f"---DECISION: GENERATION NOT GROUNDED, RETRYING ({loop_step + 1}/{max_retries})---")
                    return "not supported"
                else:
                    print("---DECISION: MAX RETRIES REACHED---")
                    raise MaxRetriesException(
                        f"Maximum de {max_retries} tentatives atteint",
                        {"loop_step": loop_step, "max_retries": max_retries}
                    )
        except MaxRetriesException:
            raise
        except Exception as e:
            print(f"⚠️ Erreur vérification hallucination: {str(e)}. On continue...")
            # En cas d'erreur, on considère comme OK pour éviter boucle infinie
        
        # Vérification de l'utilité
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        try:
            answer_grader_prompt_formatted = prompt["answer_grader_prompt"].format(
                question=state["question"],
                generation=generation_content
            )
            
            def _check_useful():
                return llm_json_mode.invoke(
                    [SystemMessage(content=prompt["answer_grader_instructions"])] +
                    [HumanMessage(content=answer_grader_prompt_formatted)]
                )
            
            result = retry_with_backoff(_check_useful)
            
            try:
                grade_data = json.loads(result.content)
                grade = grade_data.get("binary_score", "no")
            except json.JSONDecodeError:
                print("⚠️ Erreur parsing JSON answer. Par défaut: no")
                grade = "no"
            
            return "useful" if grade == "yes" else "not useful"
        except Exception as e:
            print(f"⚠️ Erreur vérification utilité: {str(e)}. Par défaut: not useful")
            return "not useful"
    except MaxRetriesException:
        return "max retries"
    except Exception as e:
        print(f"❌ Erreur dans grade_generation: {str(e)}")
        return "max retries"  # Sécurité: arrêt en cas d'erreur


# Workflow definition and graph compilation
workflow = StateGraph(GraphState)
workflow.add_node("websearch", web_search)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

workflow.set_conditional_entry_point(
    route_question,
    {"websearch": "websearch", "vectorstore": "retrieve"},
)
workflow.add_edge("websearch", "generate")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {"websearch": "websearch", "generate": "generate"},
)
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {"not supported": "generate", "useful": END, "not useful": "websearch", "max retries": END},
)

# Compile the graph
graph = workflow.compile()

# Final response function
def get_final_response(query: str) -> str:
    """Point d'entrée principal pour obtenir une réponse RAG."""
    conversation_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    # Début de la mesure end-to-end
    start_time = time.time()
    latencies = {}
    
    try:
        logger.info(
            "Request started",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id,
                "data": {"query": query[:100]}
            }
        )
        
        if not query or not query.strip():
            return "⚠️ Veuillez fournir une question valide."
        
        # Réécriture de la requête (avec fallback sur query originale)
        try:
            rewritten_query = Rewrite_query(query)
        except Exception as e:
            print(f"⚠️ Erreur réécriture, utilisation query originale: {str(e)}")
            rewritten_query = query
        
        # Initialisation de l'état avec max_retries, conversation_id et latencies
        max_retries = getattr(Config, 'MAX_RETRIES', 3)
        initial_state = GraphState(
            question=rewritten_query,
            generation="",
            web_search="No",
            max_retries=max_retries,
            answers=0,
            loop_step=0,
            documents=[],
            error_history=[],
            conversation_id=conversation_id,
            latencies=latencies
        )
        
        # Exécution du workflow
        final_state = graph.invoke(initial_state)
        
        # Récupérer les latences mises à jour depuis le state
        latencies = final_state.get("latencies", latencies)
        
        # Extraction de la réponse
        generation = final_state.get("generation")
        if generation and hasattr(generation, "content"):
            response = generation.content
        elif generation:
            response = str(generation)
        else:
            response = "⚠️ Aucune réponse générée. Veuillez reformuler votre question."
        
        # Mesurer latence end-to-end
        latencies["end_to_end"] = time.time() - start_time
        
        # Enregistrer les métriques
        if getattr(Config, 'METRICS_ENABLED', True):
            metrics.record_request(
                conversation_id=conversation_id,
                query=query,
                latencies=latencies,
                success=True,
                num_documents=len(final_state.get("documents", [])),
                response_length=len(response) if response else 0
            )
        
        logger.info(
            "Request completed",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id,
                "data": {"latency": latencies["end_to_end"]}
            }
        )
        
        return response
        
    except MaxRetriesException as e:
        latencies["end_to_end"] = time.time() - start_time
        error_msg = "⚠️ Désolé, j'ai atteint le nombre maximum de tentatives. Veuillez reformuler votre question ou réessayer plus tard."
        
        if getattr(Config, 'METRICS_ENABLED', True):
            metrics.record_request(
                conversation_id=conversation_id,
                query=query,
                latencies=latencies,
                success=False,
                error="MaxRetriesException"
            )
        
        logger.warning(
            "Request max retries",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id
            }
        )
        
        return error_msg
    
    except LLMQuotaException as e:
        latencies["end_to_end"] = time.time() - start_time
        error_msg = "⚠️ Le service est temporairement saturé. Veuillez réessayer dans quelques instants."
        
        if getattr(Config, 'METRICS_ENABLED', True):
            metrics.record_request(
                conversation_id=conversation_id,
                query=query,
                latencies=latencies,
                success=False,
                error="LLMQuotaException"
            )
        
        logger.error(
            "Request quota exceeded",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id
            }
        )
        
        return error_msg
    
    except RetrievalException as e:
        latencies["end_to_end"] = time.time() - start_time
        error_msg = "⚠️ Impossible de trouver des documents pertinents. Veuillez reformuler votre question."
        
        if getattr(Config, 'METRICS_ENABLED', True):
            metrics.record_request(
                conversation_id=conversation_id,
                query=query,
                latencies=latencies,
                success=False,
                error="RetrievalException"
            )
        
        logger.error(
            "Request retrieval failed",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id
            }
        )
        
        return error_msg
    
    except WebSearchException as e:
        latencies["end_to_end"] = time.time() - start_time
        error_msg = "⚠️ Erreur lors de la recherche web. Veuillez réessayer."
        
        if getattr(Config, 'METRICS_ENABLED', True):
            metrics.record_request(
                conversation_id=conversation_id,
                query=query,
                latencies=latencies,
                success=False,
                error="WebSearchException"
            )
        
        logger.error(
            "Request web search failed",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id
            }
        )
        
        return error_msg
        
    except Exception as e:
        latencies["end_to_end"] = time.time() - start_time
        error_msg = str(e)
        
        # Enregistrer l'erreur
        if getattr(Config, 'METRICS_ENABLED', True):
            metrics.record_request(
                conversation_id=conversation_id,
                query=query,
                latencies=latencies,
                success=False,
                error=error_msg
            )
        
        logger.error(
            "Request failed",
            extra={
                "component": "rag",
                "conversation_id": conversation_id,
                "trace_id": trace_id,
                "data": {"error": error_msg}
            },
            exc_info=True
        )
        
        raise