@echo off
REM Script pour exécuter tous les tests d'intégration API
echo ========================================
echo Tests d'integration API - RAG System
echo ========================================
echo.

REM Activer l'environnement virtuel si disponible
if exist "venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
)

REM Aller dans le répertoire Backend
cd /d "%~dp0"

echo.
echo Execution des tests d'integration...
echo.

REM Exécuter les tests avec pytest
python -m pytest tests/test_api_integration.py -v --tb=short

echo.
echo ========================================
echo Tests termines
echo ========================================
pause

