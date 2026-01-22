"""
Mécanismes de fallback avec hiérarchie de modèles.
"""
from typing import Optional
from langchain_groq import ChatGroq

from config.Config import Config


class FallbackManager:
    """Gestionnaire de fallback avec hiérarchie de modèles."""
    
    def __init__(self):
        self.models = self._initialize_models()
        self.current_model_index = 0
    
    def _initialize_models(self) -> list:
        """Initialise la hiérarchie de modèles."""
        models = []
        
        # Modèle principal
        primary_model = Config.GROQ_model
        models.append({
            "name": primary_model,
            "llm": ChatGroq(
                model_name=primary_model,
                temperature=0,
                groq_api_key=Config.GROQ_API_KEY
            ),
            "priority": 1
        })
        
        # Modèles de fallback si activés
        if getattr(Config, 'FALLBACK_MODELS_ENABLED', True):
            secondary_model = getattr(Config, 'FALLBACK_MODEL_SECONDARY', None)
            if secondary_model:
                try:
                    models.append({
                        "name": secondary_model,
                        "llm": ChatGroq(
                            model_name=secondary_model,
                            temperature=0,
                            groq_api_key=Config.GROQ_API_KEY
                        ),
                        "priority": 2
                    })
                except Exception as e:
                    print(f"[FALLBACK] Impossible d'initialiser {secondary_model}: {str(e)}")
            
            fast_model = getattr(Config, 'FALLBACK_MODEL_FAST', None)
            if fast_model:
                try:
                    models.append({
                        "name": fast_model,
                        "llm": ChatGroq(
                            model_name=fast_model,
                            temperature=0,
                            groq_api_key=Config.GROQ_API_KEY
                        ),
                        "priority": 3
                    })
                except Exception as e:
                    print(f"[FALLBACK] Impossible d'initialiser {fast_model}: {str(e)}")
        
        return models
    
    def get_current_llm(self) -> Optional[ChatGroq]:
        """Récupère le LLM actuel."""
        if self.current_model_index < len(self.models):
            return self.models[self.current_model_index]["llm"]
        return None
    
    def get_current_model_name(self) -> Optional[str]:
        """Récupère le nom du modèle actuel."""
        if self.current_model_index < len(self.models):
            return self.models[self.current_model_index]["name"]
        return None
    
    def try_next_model(self) -> bool:
        """Passe au modèle suivant dans la hiérarchie."""
        if self.current_model_index < len(self.models) - 1:
            self.current_model_index += 1
            print(f"[FALLBACK] Passage au modèle: {self.get_current_model_name()}")
            return True
        return False
    
    def reset(self):
        """Réinitialise au modèle principal."""
        self.current_model_index = 0
        print(f"[FALLBACK] Retour au modèle principal: {self.get_current_model_name()}")


# Instance globale
_fallback_manager = None


def get_fallback_manager() -> FallbackManager:
    """Récupère l'instance globale du gestionnaire de fallback."""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager