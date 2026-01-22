@echo off
echo ========================================
echo   Demarrage du Backend RAG System
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Verification de Python...
python --version
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo [2/3] Verification des dependances...
python -c "import uvicorn; import email_validator" 2>nul
if errorlevel 1 (
    echo ATTENTION: Certaines dependances peuvent manquer
    echo Installez-les avec: pip install -r requirement.txt
    echo.
)

echo [3/3] Demarrage du serveur API...
echo.
echo Le serveur va demarrer sur http://localhost:8000
echo Appuyez sur CTRL+C pour arreter
echo.
echo ========================================
echo.

python run_api.py

pause

