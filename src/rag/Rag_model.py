# Import necessary libraries
import os 
import sys
import time
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langgraph.graph import StateGraph, END
from IPython.display import Image, display
from langchain.schema import Document
from typing import List, Annotated, Dict, Optional, Callable
from typing_extensions import TypedDict
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
            _retriever = get_retriever()
            print("[INIT] ✅ Retriever créé.")
            
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
def format_docs(docs):
    """Format documents for display."""
    if not docs:
        return ""
    return "\n\n".join(doc.page_content for doc in docs if hasattr(doc, 'page_content'))


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


# Node functions
def retrieve(state: Dict) -> Dict:
    """Retrieve documents from the vector store."""
    try:
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
        start_time = time.time()
        
        try:
            print("[RETRIEVE] ⏳ Debut de retriever.invoke()...")
            documents = current_retriever.invoke(state["question"])
            elapsed_time = time.time() - start_time
            print(f"[RETRIEVE] ✅ retriever.invoke() termine avec succes en {elapsed_time:.2f}s")
        except Exception as e:
            elapsed_time = time.time() - start_time
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
            return {
                "documents": [],
                "error_history": state.get("error_history", []) + ["Aucun document trouve"]
            }
        
        print(f"[RETRIEVE] ✅ {len(documents)} documents trouves en {elapsed_time:.2f}s.")
        return {"documents": documents}
        
    except RetrievalException:
        raise
    except Exception as e:
        print(f"❌ [RETRIEVE] Exception non capturee: {str(e)}")
        import traceback
        traceback.print_exc()
        raise RetrievalException(f"Erreur recuperation: {str(e)}") from e


def generate(state: Dict) -> Dict:
    """Generate an answer using RAG on the retrieved documents."""
    try:
        print("---GENERATE---")
        
        if not state.get("documents"):
            raise GenerationException("Aucun document disponible pour la génération")
        
        docs_txt = format_docs(state["documents"])
        rag_prompt_formatted = prompt["rag_prompt"].format(
            context=docs_txt, 
            question=state["question"]
        )
        
        def _generate():
            return local_llm.invoke([HumanMessage(content=rag_prompt_formatted)])
        
        generation = retry_with_backoff(_generate)
        
        if not generation:
            raise InvalidResponseException("Réponse vide du LLM")
        
        return {
            "generation": generation,
            "loop_step": state.get("loop_step", 0) + 1
        }
    except LLMQuotaException as e:
        raise LLMQuotaException(
            "Quota API dépassé. Veuillez réessayer plus tard.",
            {"loop_step": state.get("loop_step", 0)}
        ) from e
    except Exception as e:
        error_msg = f"Erreur lors de la génération: {str(e)}"
        print(f"❌ {error_msg}")
        from src.core.exceptions import GenerationException
        raise GenerationException(error_msg) from e


def grade_documents(state: Dict) -> Dict:
    """Grade the relevance of retrieved documents."""
    try:
        print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
        filtered_docs = []
        web_search = "No"
        
        if not state.get("documents"):
            return {"documents": [], "web_search": "Yes"}
        
        for doc in state["documents"]:
            try:
                doc_grader_prompt_formatted = prompt["doc_grader_prompt"].format(
                    document=doc.page_content, 
                    question=state["question"]
                )
                
                def _grade():
                    return llm_json_mode.invoke(
                        [SystemMessage(content=prompt["doc_grader_instructions"])] +
                        [HumanMessage(content=doc_grader_prompt_formatted)]
                    )
                
                result = retry_with_backoff(_grade)
                
                # Parse JSON avec gestion d'erreur
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
        
        return {"documents": filtered_docs, "web_search": web_search}
    except Exception as e:
        print(f"❌ Erreur dans grade_documents: {str(e)}")
        # En cas d'erreur, on continue avec tous les documents
        return {"documents": state.get("documents", []), "web_search": "Yes"}


def web_search(state: Dict) -> Dict:
    """Perform a web search based on the question."""
    try:
        print("---WEB SEARCH---")
        
        if not state.get("question"):
            raise WebSearchException("Question manquante pour la recherche web")
        
        def _search():
            return web_search_tool.invoke({"query": state["question"]})
        
        docs = retry_with_backoff(_search, max_retries=2)
        
        if not docs:
            print("⚠️ Aucun résultat de recherche web")
            return {"documents": state.get("documents", [])}
        
        web_results = "\n".join([d.get("content", "") for d in docs if d.get("content")])
        
        if not web_results:
            print("⚠️ Résultats web vides")
            return {"documents": state.get("documents", [])}
        
        documents = state.get("documents", [])
        documents.append(Document(page_content=web_results))
        
        return {"documents": documents}
    except Exception as e:
        error_msg = f"Erreur lors de la recherche web: {str(e)}"
        print(f"❌ {error_msg}")
        # Ne pas bloquer, continuer avec les documents existants
        return {"documents": state.get("documents", [])}


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
                documents=format_docs(state.get("documents", [])),
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
    """Run the workflow and return the final generated response."""
    try:
        if not query or not query.strip():
            return "⚠️ Veuillez fournir une question valide."
        
        # Réécriture de la requête (avec fallback sur query originale)
        try:
            rewritten_query = Rewrite_query(query)
        except Exception as e:
            print(f"⚠️ Erreur réécriture, utilisation query originale: {str(e)}")
            rewritten_query = query
        
        # Initialisation de l'état avec max_retries
        max_retries = getattr(Config, 'MAX_RETRIES', 3)
        initial_state = GraphState(
            question=rewritten_query,
            generation="",
            web_search="No",
            max_retries=max_retries,
            answers=0,
            loop_step=0,
            documents=[],
            error_history=[]
        )
        
        # Exécution du workflow
        final_state = graph.invoke(initial_state)
        
        # Extraction de la réponse
        generation = final_state.get("generation")
        if generation and hasattr(generation, "content"):
            return generation.content
        elif generation:
            return str(generation)
        else:
            return "⚠️ Aucune réponse générée. Veuillez reformuler votre question."
    
    except MaxRetriesException as e:
        return "⚠️ Désolé, j'ai atteint le nombre maximum de tentatives. Veuillez reformuler votre question ou réessayer plus tard."
    
    except LLMQuotaException as e:
        return "⚠️ Le service est temporairement saturé. Veuillez réessayer dans quelques instants."
    
    except RetrievalException as e:
        return "⚠️ Impossible de trouver des documents pertinents. Veuillez reformuler votre question."
    
    except WebSearchException as e:
        return "⚠️ Erreur lors de la recherche web. Veuillez réessayer."
    
    except Exception as e:
        error_msg = f"Une erreur inattendue s'est produite: {str(e)}"
        print(f"❌ {error_msg}")
        return "⚠️ Une erreur technique s'est produite. Veuillez réessayer ou contacter le support si le problème persiste."