"""
Gestionnaire de rotation des clés API Groq avec fallback automatique.
"""
import time
from typing import List, Optional, Dict
from langchain_groq import ChatGroq
from config.Config import Config
from langchain_core.messages import BaseMessage

class GroqKeyManager:
    """Gère la rotation des clés API Groq avec détection des rate limits."""
    
    def __init__(self):
        # Récupérer toutes les clés API
        main_key = getattr(Config, 'GROQ_API_KEY', None)
        additional_keys = getattr(Config, 'GROQ_API_KEYS', [])
        
        # Construire la liste complète des clés
        all_keys = []
        if main_key:
            all_keys.append(main_key)
        if additional_keys:
            all_keys.extend(additional_keys)
        
        # Supprimer les doublons en gardant l'ordre
        self.api_keys = list(dict.fromkeys([key.strip() for key in all_keys if key and key.strip()]))
        
        if not self.api_keys:
            raise ValueError("Aucune clé API Groq configurée. Vérifiez GROQ_API_KEY ou GROQ_API_KEYS dans .env")
        
        self.current_key_index = 0
        self.key_status: Dict[str, Dict] = {}  # {key: {'blocked_until': timestamp, 'error_count': int}}
        self.model_name = getattr(Config, 'GROQ_model', 'openai/gpt-oss-120b')
        self._llm_cache: Dict[str, ChatGroq] = {}  # Cache des instances LLM par clé
        
        print(f"[GroqKeyManager] {len(self.api_keys)} clé(s) API configurée(s)")
    
    def get_current_key(self) -> str:
        """Récupère la clé API actuellement active."""
        return self.api_keys[self.current_key_index]
    
    def get_current_llm(self, json_mode: bool = False) -> ChatGroq:
        """Récupère l'instance LLM avec la clé actuelle."""
        key = self.get_current_key()
        cache_key = f"{key}_{json_mode}"
        
        if cache_key not in self._llm_cache:
            model_kwargs = {}
            if json_mode:
                model_kwargs = {"response_format": {"type": "json_object"}}
            
            self._llm_cache[cache_key] = ChatGroq(
                model_name=self.model_name,
                temperature=0,
                groq_api_key=key,
                model_kwargs=model_kwargs
            )
        
        return self._llm_cache[cache_key]
    
    def is_key_blocked(self, key: str) -> bool:
        """Vérifie si une clé est temporairement bloquée (rate limit)."""
        if key not in self.key_status:
            return False
        
        blocked_until = self.key_status[key].get('blocked_until', 0)
        return time.time() < blocked_until
    
    def block_key(self, key: str, duration_seconds: int = 420):
        """Bloque une clé pour une durée donnée (par défaut 7 minutes)."""
        if key not in self.key_status:
            self.key_status[key] = {'error_count': 0, 'blocked_until': 0}
        
        self.key_status[key]['blocked_until'] = time.time() + duration_seconds
        self.key_status[key]['error_count'] = self.key_status[key].get('error_count', 0) + 1
        
        print(f"⚠️ [GroqKeyManager] Clé API bloquée pour {duration_seconds}s (rate limit atteint)")
    
    def unblock_key(self, key: str):
        """Débloque une clé."""
        if key in self.key_status:
            self.key_status[key]['blocked_until'] = 0
    
    def rotate_to_next_key(self) -> bool:
        """Passe à la clé suivante. Retourne True si une clé valide est trouvée."""
        original_index = self.current_key_index
        attempts = 0
        
        while attempts < len(self.api_keys):
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            next_key = self.get_current_key()
            
            if not self.is_key_blocked(next_key):
                if self.current_key_index != original_index:
                    print(f"🔄 [GroqKeyManager] Rotation vers clé API #{self.current_key_index + 1}/{len(self.api_keys)}")
                return True
            
            attempts += 1
        
        # Toutes les clés sont bloquées
        print(f"❌ [GroqKeyManager] Toutes les clés API sont bloquées. Attente nécessaire.")
        return False
    
    def handle_rate_limit_error(self, error: Exception) -> bool:
        """Gère une erreur de rate limit et change de clé si possible."""
        error_str = str(error)
        
        # Détecter les erreurs 429 (rate limit)
        if '429' in error_str or 'rate_limit' in error_str.lower() or 'Rate limit' in error_str:
            current_key = self.get_current_key()
            
            # Extraire la durée d'attente si disponible dans le message d'erreur
            duration = 420  # Par défaut 7 minutes
            if 'try again in' in error_str.lower():
                # Essayer d'extraire le temps d'attente
                import re
                match = re.search(r'try again in (\d+)m?(\d+\.?\d*)s?', error_str.lower())
                if match:
                    minutes = int(match.group(1)) if match.group(1) else 0
                    seconds = float(match.group(2)) if len(match.groups()) > 1 and match.group(2) else 0
                    duration = int(minutes * 60 + seconds) + 10  # Ajouter 10s de marge
            
            self.block_key(current_key, duration)
            
            # Essayer de passer à la clé suivante
            if self.rotate_to_next_key():
                return True  # Nouvelle clé disponible
            else:
                return False  # Toutes les clés sont bloquées
        
        return False
    
    def invoke_with_fallback(self, messages: List[BaseMessage], json_mode: bool = False, max_retries: int = None):
        """
        Invoke le LLM avec fallback automatique sur les autres clés en cas de rate limit.
        
        Args:
            messages: Messages à envoyer au LLM
            json_mode: Si True, utilise le mode JSON
            max_retries: Nombre maximum de tentatives (None = nombre de clés disponibles)
        
        Returns:
            Réponse du LLM
        
        Raises:
            Exception: Si toutes les clés sont épuisées
        """
        if max_retries is None:
            max_retries = len(self.api_keys)
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                llm = self.get_current_llm(json_mode=json_mode)
                return llm.invoke(messages)
            
            except Exception as e:
                last_error = e
                
                # Vérifier si c'est une erreur de rate limit
                if self.handle_rate_limit_error(e):
                    # Nouvelle clé disponible, réessayer
                    continue
                else:
                    # Erreur non liée au rate limit ou toutes les clés bloquées
                    if '429' not in str(e) and 'rate_limit' not in str(e).lower():
                        # Erreur non liée au rate limit, propager
                        raise e
                    # Sinon, continuer pour essayer une autre clé
        
        # Toutes les tentatives échouées
        raise Exception(f"Toutes les clés API Groq sont épuisées. Dernière erreur: {str(last_error)}")
    
    def stream_with_fallback(self, messages: List[BaseMessage], json_mode: bool = False, max_retries: int = None):
        """
        Stream le LLM avec fallback automatique sur les autres clés en cas de rate limit.
        
        Args:
            messages: Messages à envoyer au LLM
            json_mode: Si True, utilise le mode JSON
            max_retries: Nombre maximum de tentatives
        
        Yields:
            Chunks de la réponse du LLM
        
        Raises:
            Exception: Si toutes les clés sont épuisées
        """
        if max_retries is None:
            max_retries = len(self.api_keys)
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                llm = self.get_current_llm(json_mode=json_mode)
                for chunk in llm.stream(messages):
                    yield chunk
                return  # Succès
            
            except Exception as e:
                last_error = e
                
                # Vérifier si c'est une erreur de rate limit
                if self.handle_rate_limit_error(e):
                    # Nouvelle clé disponible, réessayer
                    continue
                else:
                    # Erreur non liée au rate limit ou toutes les clés bloquées
                    if '429' not in str(e) and 'rate_limit' not in str(e).lower():
                        # Erreur non liée au rate limit, propager
                        raise e
                    # Sinon, continuer pour essayer une autre clé
        
        # Toutes les tentatives échouées
        raise Exception(f"Toutes les clés API Groq sont épuisées. Dernière erreur: {str(last_error)}")


# Instance globale
_groq_key_manager = None

def get_groq_key_manager() -> GroqKeyManager:
    """Récupère l'instance globale du gestionnaire de clés."""
    global _groq_key_manager
    if _groq_key_manager is None:
        _groq_key_manager = GroqKeyManager()
    return _groq_key_manager

