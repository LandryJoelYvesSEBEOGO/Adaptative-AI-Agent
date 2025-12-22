"""
Module pour la gestion sophistiquée des retries avec circuit breaker et stratégies de recovery.
"""
import time
import random
import threading
from enum import Enum
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta

from config.Config import Config
from src.core.exceptions import MaxRetriesException


class CircuitState(Enum):
    """États du circuit breaker."""
    CLOSED = "closed"  # Circuit normal, requêtes passent
    OPEN = "open"  # Circuit ouvert, requêtes bloquées
    HALF_OPEN = "half_open"  # Circuit en test, quelques requêtes passent


class CircuitBreaker:
    """Circuit breaker pattern pour éviter les appels répétés à un service défaillant."""
    
    def __init__(self, 
                 failure_threshold: int = None,
                 recovery_timeout: int = None,
                 half_open_max_calls: int = None):
        self.failure_threshold = failure_threshold or getattr(Config, 'CIRCUIT_BREAKER_FAILURE_THRESHOLD', 5)
        self.recovery_timeout = recovery_timeout or getattr(Config, 'CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60)
        self.half_open_max_calls = half_open_max_calls or getattr(Config, 'CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS', 3)
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Exécute une fonction avec protection du circuit breaker."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                # Vérifier si on peut passer en half-open
                if self.last_failure_time and \
                   (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    print(f"[CIRCUIT BREAKER] Passage en HALF_OPEN après {self.recovery_timeout}s")
                else:
                    raise MaxRetriesException(
                        f"Circuit breaker OPEN. Service indisponible. "
                        f"Réessayez dans {self.recovery_timeout - (datetime.now() - self.last_failure_time).total_seconds():.0f}s"
                    )
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    # Trop d'appels en half-open, retourner à OPEN
                    self.state = CircuitState.OPEN
                    self.last_failure_time = datetime.now()
                    raise MaxRetriesException("Circuit breaker retourné à OPEN après trop d'appels")
                self.half_open_calls += 1
        
        # Exécuter la fonction
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Appelé lors d'un succès."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                # Succès en half-open, fermer le circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
                print("[CIRCUIT BREAKER] Circuit fermé après succès en HALF_OPEN")
            elif self.state == CircuitState.CLOSED:
                # Réinitialiser le compteur d'échecs
                self.failure_count = 0
    
    def _on_failure(self):
        """Appelé lors d'un échec."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Échec en half-open, retourner à OPEN
                self.state = CircuitState.OPEN
                self.half_open_calls = 0
                print("[CIRCUIT BREAKER] Échec en HALF_OPEN, retour à OPEN")
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                # Trop d'échecs, ouvrir le circuit
                self.state = CircuitState.OPEN
                print(f"[CIRCUIT BREAKER] Circuit ouvert après {self.failure_count} échecs")
    
    def reset(self):
        """Réinitialise le circuit breaker."""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.half_open_calls = 0


# Circuit breakers globaux par type de service
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Récupère ou crée un circuit breaker pour un service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker()
    return _circuit_breakers[service_name]


def retry_with_backoff_advanced(
    func: Callable,
    max_retries: int = None,
    initial_delay: int = None,
    backoff_factor: float = None,
    jitter_enabled: bool = None,
    jitter_max: float = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    retryable_exceptions: tuple = None
) -> Any:
    """
    Retry une fonction avec backoff exponentiel, jitter et circuit breaker.
    
    Args:
        func: Fonction à exécuter
        max_retries: Nombre maximum de tentatives
        initial_delay: Délai initial en secondes
        backoff_factor: Facteur d'exponentiel backoff
        jitter_enabled: Activer le jitter aléatoire
        jitter_max: Jitter maximum (fraction du délai)
        circuit_breaker: Circuit breaker à utiliser (optionnel)
        retryable_exceptions: Exceptions qui doivent déclencher un retry
    
    Returns:
        Résultat de la fonction
    
    Raises:
        MaxRetriesException: Si toutes les tentatives échouent
    """
    if max_retries is None:
        max_retries = getattr(Config, 'MAX_RETRIES', 3)
    if initial_delay is None:
        initial_delay = getattr(Config, 'RETRY_INITIAL_DELAY', 1)
    if backoff_factor is None:
        backoff_factor = getattr(Config, 'RETRY_BACKOFF_FACTOR', 2)
    if jitter_enabled is None:
        jitter_enabled = getattr(Config, 'RETRY_JITTER_ENABLED', True)
    if jitter_max is None:
        jitter_max = getattr(Config, 'RETRY_JITTER_MAX', 0.3)
    if retryable_exceptions is None:
        from src.core.exceptions import (
            LLMTimeoutException, LLMQuotaException, LLMAPIException
        )
        retryable_exceptions = (LLMTimeoutException, LLMAPIException)
    
    # Utiliser le circuit breaker si fourni
    if circuit_breaker:
        try:
            return circuit_breaker.call(func)
        except MaxRetriesException:
            raise
    
    # Retry avec backoff et jitter
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except retryable_exceptions + (Exception,) as e:
            last_exception = e
            
            # Ne pas retry pour certaines exceptions
            if isinstance(e, MaxRetriesException):
                raise
            
            if attempt == max_retries - 1:
                # Dernière tentative, lever l'exception
                break
            
            # Calculer le délai avec backoff exponentiel
            delay = initial_delay * (backoff_factor ** attempt)
            
            # Ajouter du jitter si activé
            if jitter_enabled:
                jitter = random.uniform(0, jitter_max) * delay
                delay = delay + jitter
            
            print(f"⚠️ Tentative {attempt + 1}/{max_retries} échouée ({type(e).__name__}). Retry dans {delay:.2f}s...")
            time.sleep(delay)
    
    # Toutes les tentatives ont échoué
    raise MaxRetriesException(f"Échec après {max_retries} tentatives: {str(last_exception)}") from last_exception