"""
Module pour gérer les templates de prompts dynamiques et role-based prompting.
"""
import re
from typing import Dict, Optional
from config.Config import Config

# Rôles prédéfinis selon le contexte
ROLES = {
    "technical": {
        "role": "technical documentation expert",
        "tone": "precise and professional",
        "style": "clear and structured"
    },
    "academic": {
        "role": "academic researcher",
        "tone": "scholarly and rigorous",
        "style": "comprehensive and well-cited"
    },
    "general": {
        "role": "helpful assistant",
        "tone": "friendly and clear",
        "style": "concise and accessible"
    },
    "code": {
        "role": "software engineering expert",
        "tone": "technical and practical",
        "style": "code-focused with examples"
    }
}

def detect_role_from_question(question: str) -> str:
    """
    Détecte le rôle approprié selon la question.
    
    Args:
        question: La question de l'utilisateur
    
    Returns:
        Clé du rôle ('technical', 'academic', 'code', 'general')
    """
    question_lower = question.lower()
    
    # Mots-clés pour détection
    code_keywords = ['code', 'programming', 'function', 'class', 'api', 'syntax', 'algorithm']
    academic_keywords = ['research', 'study', 'analysis', 'methodology', 'theoretical', 'hypothesis']
    technical_keywords = ['implementation', 'architecture', 'system', 'design', 'framework', 'protocol']
    
    if any(keyword in question_lower for keyword in code_keywords):
        return "code"
    elif any(keyword in question_lower for keyword in academic_keywords):
        return "academic"
    elif any(keyword in question_lower for keyword in technical_keywords):
        return "technical"
    else:
        return "general"

def get_role_prompt(role_key: Optional[str] = None) -> str:
    """
    Génère le préfixe de rôle pour le prompt.
    
    Args:
        role_key: Clé du rôle ('technical', 'academic', etc.) ou None pour auto-détection
    
    Returns:
        Chaîne de rôle formatée
    """
    if not getattr(Config, 'ROLE_BASED_PROMPTING_ENABLED', True):
        return ""
    
    if role_key is None:
        if getattr(Config, 'ROLE_DETECTION_ENABLED', True):
            # Auto-détection sera faite lors de l'utilisation
            return ""  # Sera déterminé dynamiquement
        else:
            role_key = "general"
    
    role_info = ROLES.get(role_key, ROLES["general"])
    
    return f"""You are a {role_info['role']}. 
Your responses should be {role_info['tone']} and written in a {role_info['style']} style.

"""

def get_chain_of_thought_instruction(question: str) -> str:
    """
    Génère l'instruction Chain-of-Thought si nécessaire.
    
    Args:
        question: La question de l'utilisateur
    
    Returns:
        Instruction CoT ou chaîne vide
    """
    if not getattr(Config, 'CHAIN_OF_THOUGHT_ENABLED', True):
        return ""
    
    # Décider si la question est complexe
    is_complex = False
    if getattr(Config, 'CHAIN_OF_THOUGHT_FOR_COMPLEX', True):
        word_count = len(question.split())
        complexity_threshold = getattr(Config, 'CHAIN_OF_THOUGHT_COMPLEXITY_THRESHOLD', 50)
        is_complex = word_count > complexity_threshold or \
                     any(word in question.lower() for word in ['how', 'why', 'explain', 'compare', 'analyze'])
    else:
        is_complex = True  # Toujours activer si pas de filtre
    
    if is_complex:
        return """
IMPORTANT: Think step by step before providing your answer:
1. First, identify the key concepts and requirements in the question
2. Then, analyze the relevant information from the context
3. Finally, synthesize your answer based on your reasoning

"""
    return ""

def format_structured_output_instruction() -> str:
    """
    Génère l'instruction pour structured output.
    
    Returns:
        Instruction formatée ou chaîne vide
    """
    if not getattr(Config, 'STRUCTURED_OUTPUT_ENABLED', False):
        return ""
    
    output_format = getattr(Config, 'STRUCTURED_OUTPUT_FORMAT', 'markdown')
    
    if output_format == "markdown":
        return """
Please format your answer using Markdown:
- Use headers for main sections
- Use bullet points or numbered lists for details
- Use code blocks for technical examples
- Use **bold** for emphasis on key points

"""
    elif output_format == "json":
        return """
Please provide your answer in JSON format with the following structure:
{
    "summary": "Brief summary",
    "details": ["point 1", "point 2"],
    "examples": ["example 1", "example 2"]
}

"""
    return ""