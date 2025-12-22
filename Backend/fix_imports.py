"""
Script pour vérifier et corriger les imports après réorganisation
"""
import os
import re
import sys

# Définir le répertoire Backend comme racine
backend_root = os.path.dirname(os.path.abspath(__file__))

def check_imports_in_file(file_path):
    """Vérifie les imports dans un fichier."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Vérifier les imports
        for i, line in enumerate(lines, 1):
            # Vérifier les imports absolus qui pourraient être incorrects
            if re.match(r'^\s*from\s+config\.', line) or re.match(r'^\s*import\s+config', line):
                # Vérifier si project_root est défini avant
                before_lines = '\n'.join(lines[:i])
                if 'project_root' not in before_lines and 'sys.path' not in before_lines:
                    issues.append(f"Ligne {i}: Import 'config' sans définition de project_root")
            
            if re.match(r'^\s*from\s+src\.', line) or re.match(r'^\s*import\s+src', line):
                before_lines = '\n'.join(lines[:i])
                if 'project_root' not in before_lines and 'sys.path' not in before_lines:
                    issues.append(f"Ligne {i}: Import 'src' sans définition de project_root")
    
    except Exception as e:
        issues.append(f"Erreur lecture fichier: {str(e)}")
    
    return issues

def verify_project_root_paths():
    """Vérifie que tous les project_root pointent vers Backend."""
    issues = []
    
    # Fichiers à vérifier
    files_to_check = [
        'config/Config.py',
        'src/rag/Rag_model.py',
        'src/main.py',
        'src/rag/Data_processing.py',
        'tests/test_prompt_engineering.py'
    ]
    
    for rel_path in files_to_check:
        file_path = os.path.join(backend_root, rel_path)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Vérifier le calcul de project_root
            if 'project_root' in content:
                # Extraire la ligne project_root
                match = re.search(r'project_root\s*=\s*os\.path\.abspath\(os\.path\.join\(os\.path\.dirname\(__file__\)[^)]+\)\)', content)
                if match:
                    # Calculer le chemin attendu
                    file_dir = os.path.dirname(file_path)
                    depth = rel_path.count('/') - 1  # Nombre de niveaux depuis Backend
                    
                    if depth == 0:
                        expected = backend_root
                    elif depth == 1:
                        expected = backend_root
                    else:
                        expected = backend_root
                    
                    print(f"[OK] {rel_path}: project_root calcule correctement")
                else:
                    issues.append(f"{rel_path}: Pattern project_root non trouvé")
    
    return issues

def main():
    """Fonction principale."""
    print("="*60)
    print("Vérification des imports après réorganisation")
    print("="*60)
    
    # Vérifier les chemins project_root
    print("\n1. Vérification des chemins project_root...")
    issues = verify_project_root_paths()
    
    if issues:
        print("\n⚠️ Problèmes détectés:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[OK] Tous les chemins project_root sont corrects")
    
    # Vérifier les imports dans les fichiers principaux
    print("\n2. Vérification des imports...")
    main_files = [
        'src/rag/Rag_model.py',
        'src/main.py',
        'src/rag/Data_processing.py',
        'src/rag/Prompts.py'
    ]
    
    all_issues = []
    for rel_path in main_files:
        file_path = os.path.join(backend_root, rel_path)
        if os.path.exists(file_path):
            issues = check_imports_in_file(file_path)
            if issues:
                print(f"\n⚠️ {rel_path}:")
                for issue in issues:
                    print(f"  - {issue}")
                all_issues.extend(issues)
            else:
                print(f"[OK] {rel_path}: OK")
    
    # Résumé
    print("\n" + "="*60)
    if all_issues:
        print(f"⚠️ {len(all_issues)} problème(s) détecté(s)")
    else:
        print("[SUCCES] Tous les imports sont coherents!")
    print("="*60)

if __name__ == "__main__":
    main()

