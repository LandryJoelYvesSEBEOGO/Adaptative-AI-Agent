"""
Hiérarchie d'exceptions personnalisées pour le système RAG.
"""
from typing import Optional


class RAGException(Exception):
    """Exception de base pour toutes les erreurs RAG."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class RetrievalException(RAGException):
    """Exception lors de la récupération de documents."""
    pass


class VectorStoreException(RetrievalException):
    """Erreur avec la base vectorielle (ChromaDB)."""
    pass


class EmbeddingException(RetrievalException):
    """Erreur lors de la génération d'embeddings."""
    pass


class DocumentNotFoundException(RetrievalException):
    """Aucun document trouvé pour la requête."""
    pass


class GenerationException(RAGException):
    """Exception lors de la génération de réponse."""
    pass


class LLMTimeoutException(GenerationException):
    """Timeout lors de l'appel au LLM."""
    pass


class LLMQuotaException(GenerationException):
    """Quota API dépassé."""
    pass


class LLMAPIException(GenerationException):
    """Erreur générique de l'API LLM."""
    pass


class InvalidResponseException(GenerationException):
    """Réponse invalide du LLM (format incorrect)."""
    pass


class ValidationException(RAGException):
    """Exception lors de la validation."""
    pass


class HallucinationDetectedException(ValidationException):
    """Hallucination détectée dans la réponse."""
    pass


class LowQualityException(ValidationException):
    """Qualité de la réponse insuffisante."""
    pass


class WorkflowException(RAGException):
    """Exception dans le workflow."""
    pass


class MaxRetriesException(WorkflowException):
    """Nombre maximum de tentatives atteint."""
    pass


class StateCorruptionException(WorkflowException):
    """État du workflow corrompu."""
    pass


class WebSearchException(RAGException):
    """Exception lors de la recherche web."""
    pass