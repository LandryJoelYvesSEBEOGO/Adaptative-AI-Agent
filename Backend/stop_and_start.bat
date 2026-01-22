@echo off
echo ========================================
echo   Arret et Redemarrage du Backend
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Recherche des processus sur le port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Processus trouve: PID %%a
    echo.
    echo Arret du processus...
    taskkill /PID %%a /F >nul 2>&1
    if errorlevel 1 (
        echo ATTENTION: Impossible d'arreter le processus. Essayez en tant qu'administrateur.
    ) else (
        echo SUCCES: Processus arrete.
    )
    timeout /t 2 >nul
)

echo.
echo [2/3] Verification que le port est libre...
timeout /t 1 >nul
netstat -ano | findstr :8000 >nul
if errorlevel 1 (
    echo Port 8000 est maintenant libre.
) else (
    echo ATTENTION: Le port 8000 est toujours occupe.
    echo Vous devrez peut-etre redemarrer votre ordinateur.
)

echo.
echo [3/3] Demarrage du backend...
echo.
echo Le serveur va demarrer sur http://localhost:8000
echo Appuyez sur CTRL+C pour arreter
echo.
echo ========================================
echo.

python run_api.py

pause

