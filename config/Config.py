from dotenv import load_dotenv
import os

# Chargement des variables d'environnement
load_dotenv()

# Définir project_root pour les chemins
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:

    # Configuration des environnemnt
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "local-llama32-rag"
    os.environ["TOKENIZERS_PARALLELISM"] = "true"
    os.environ["USER_AGENT"] = "MyCustomUserAgent/1.0"
    
    #Configuration des Keys 
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    #Configuration des models 
    GROQ_model="openai/gpt-oss-120b"
    NomicEmbeddings_model="nomic-embed-text-v1.5"

        # Configuration du workflow
    MAX_RETRIES = 3  # Nombre maximum de tentatives en cas d'échec
    RETRY_BACKOFF_FACTOR = 2  # Facteur d'exponentiel backoff
    RETRY_INITIAL_DELAY = 1  # Délai initial en secondes
    
    # Timeouts (en secondes)
    LLM_TIMEOUT = 30
    RETRIEVAL_TIMEOUT = 10
    WEB_SEARCH_TIMEOUT = 15

        # Configuration des métriques
    METRICS_ENABLED = True  # Activer/désactiver les métriques
    METRICS_DIR = os.path.join(project_root, "data", "metrics")
    LOGS_DIR = os.path.join(project_root, "data", "logs")
    
    # Seuils d'alerte (en secondes)
    ALERT_LATENCY_THRESHOLD = 10.0  # Alerter si latence > 10s
    ALERT_ERROR_RATE_THRESHOLD = 0.05  # Alerter si taux d'erreur > 5%


# Global variables
class SPEAKER_TYPES:
  USER = "user"
  BOT = "bot"


#if __name__ == "__main__":
    #print(Config.GROQ_API_KEY)
    #print(Config.GROQ_model)
    #print(Config.NomicEmbeddings_model)
    #print(Config.TAVILY_API_KEY)
    #print(Config.LANGSMITH_API_KEY)
    #print(SPEAKER_TYPES.USER)
    #print(SPEAKER_TYPES.BOT)

    # Data_processing.py

#print("Nom du module :", __name__)
#print("Package du module :", __package__)
