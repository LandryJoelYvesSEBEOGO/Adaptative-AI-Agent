@echo off
echo ========================================
echo   Verification du Port 8000
echo ========================================
echo.

echo Recherche des processus utilisant le port 8000...
echo.

netstat -ano | findstr :8000

if errorlevel 1 (
    echo.
    echo Le port 8000 est LIBRE - Vous pouvez demarrer le backend
) else (
    echo.
    echo Le port 8000 est OCCUPE
    echo.
    echo Pour liberer le port, trouvez le PID dans la colonne de droite
    echo puis executez: taskkill /PID <PID> /F
    echo.
    echo ATTENTION: Cela va arreter le processus utilisant le port 8000
)

echo.
pause

