"""
Logger structuré JSON pour le système RAG.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import sys

# Répertoire pour les logs
LOGS_DIR = Path(__file__).parent.parent.parent / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Fichier de log
LOG_FILE = LOGS_DIR / "rag.log"


class JSONFormatter(logging.Formatter):
    """Formatter qui produit des logs JSON structurés."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formate un log record en JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": "rag-chatbot",
            "component": getattr(record, "component", "unknown"),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Ajouter des champs supplémentaires si présents
        if hasattr(record, "conversation_id"):
            log_data["conversation_id"] = record.conversation_id
        
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        
        if hasattr(record, "data"):
            log_data["data"] = record.data
        
        # Ajouter exception si présente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = "rag",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Configure et retourne un logger structuré.
    
    Args:
        name: Nom du logger
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si True, écrit dans un fichier
        log_to_console: Si True, écrit dans la console
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Éviter les handlers dupliqués
    if logger.handlers:
        return logger
    
    formatter = JSONFormatter()
    
    # Handler pour fichier
    if log_to_file:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Handler pour console (format simple pour lisibilité)
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        # Format simple pour console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(component)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


# Logger global
_logger = None

def get_logger() -> logging.Logger:
    """Récupère le logger global."""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger