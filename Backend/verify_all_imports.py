"""
Script pour vérifier que tous les imports fonctionnent correctement
"""
import os
import sys

# Ajouter Backend au path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

print("="*60)
print("Verification de tous les imports")
print("="*60)

errors = []
success = []

# Test 1: Config
try:
    from config.Config import Config
    print("[OK] Import Config: SUCCES")
    success.append("Config")
except Exception as e:
    print(f"[ERREUR] Import Config: {str(e)}")
    errors.append(("Config", str(e)))

# Test 2: Core modules
core_modules = [
    ("src.core.exceptions", "exceptions"),
    ("src.core.metrics", "metrics"),
    ("src.core.logger", "logger"),
    ("src.core.retry_policy", "retry_policy"),
    ("src.core.fallback", "fallback"),
    ("src.core.recovery_strategies", "recovery_strategies"),
    ("src.core.few_shot_examples", "few_shot_examples"),
    ("src.core.prompt_templates", "prompt_templates"),
    ("src.core.retrieval_metrics", "retrieval_metrics"),
]

for module_path, module_name in core_modules:
    try:
        __import__(module_path)
        print(f"[OK] Import {module_name}: SUCCES")
        success.append(module_name)
    except Exception as e:
        print(f"[ERREUR] Import {module_name}: {str(e)}")
        errors.append((module_name, str(e)))

# Test 3: RAG modules
rag_modules = [
    ("src.rag.Prompts", "Prompts"),
    ("src.rag.Data_processing", "Data_processing"),
    ("src.rag.Rag_model", "Rag_model"),
]

for module_path, module_name in rag_modules:
    try:
        __import__(module_path)
        print(f"[OK] Import {module_name}: SUCCES")
        success.append(module_name)
    except Exception as e:
        print(f"[ERREUR] Import {module_name}: {str(e)}")
        errors.append((module_name, str(e)))

# Test 4: Main
try:
    import src.main
    print("[OK] Import main: SUCCES")
    success.append("main")
except Exception as e:
    print(f"[ERREUR] Import main: {str(e)}")
    errors.append(("main", str(e)))

# Résumé
print("\n" + "="*60)
print(f"SUCCES: {len(success)}/{len(success) + len(errors)}")
print(f"ERREURS: {len(errors)}/{len(success) + len(errors)}")
print("="*60)

if errors:
    print("\nDetails des erreurs:")
    for module, error in errors:
        print(f"  - {module}: {error}")
    sys.exit(1)
else:
    print("\n[SUCCES] Tous les imports fonctionnent correctement!")
    sys.exit(0)

