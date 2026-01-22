@echo off
echo ========================================
echo   Liberation du Port 8000
echo ========================================
echo.

echo Recherche des processus utilisant le port 8000...
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo Processus trouve avec PID: %%a
    echo.
    set /p confirm="Voulez-vous arreter ce processus? (O/N): "
    if /i "!confirm!"=="O" (
        echo.
        echo Arret du processus PID %%a...
        taskkill /PID %%a /F
        if errorlevel 1 (
            echo ERREUR: Impossible d'arreter le processus. Vous devez peut-etre executer en tant qu'administrateur.
        ) else (
            echo SUCCES: Le processus a ete arrete.
            echo Le port 8000 est maintenant libre.
        )
    ) else (
        echo Operation annulee.
    )
    goto :end
)

echo Aucun processus trouve sur le port 8000.

:end
echo.
pause

