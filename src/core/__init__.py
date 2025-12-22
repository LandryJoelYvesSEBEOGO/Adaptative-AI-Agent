# src/core/__init__.py
from .exceptions import (
    RAGException,
    RetrievalException,
    GenerationException,
    ValidationException,
    WorkflowException
)

# Metrics and logging
from .metrics import get_metrics_collector
from .logger import get_logger
from .retrieval_metrics import (
    get_retrieval_metrics_collector,
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_mean_average_precision,
    calculate_retrieval_metrics
)
from src.core.retry_policy import (
    retry_with_backoff_advanced,
    get_circuit_breaker,
    CircuitBreaker,
    CircuitState
)
from src.core.recovery_strategies import RecoveryStrategy
from src.core.fallback import get_fallback_manager, FallbackManager

__all__ = [
    "RAGException",
    "RetrievalException",
    "GenerationException",
    "ValidationException",
    "WorkflowException",
    "get_metrics_collector",
    "get_logger",
    "get_retrieval_metrics_collector",
    "calculate_precision_at_k",
    "calculate_recall_at_k",
    "calculate_mean_average_precision",
    "calculate_retrieval_metrics",
    "retry_with_backoff_advanced",
    "get_circuit_breaker",
    "CircuitBreaker",
    "CircuitState",
    "RecoveryStrategy",
    "get_fallback_manager",
    "FallbackManager"
]