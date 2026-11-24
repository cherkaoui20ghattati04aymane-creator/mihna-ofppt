@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo ERREUR : environnement Python absent. Lancez d'abord INSTALLER_WINDOWS.bat.
  pause
  exit /b 1
)
echo Execution de tous les tests automatises (aucun appel reseau, bases temporaires)...
".venv\Scripts\python.exe" -m pytest -q -rs tests auth_gateway\tests
if errorlevel 1 (
  echo.
  echo Certains tests ont echoue : consultez le detail ci-dessus.
) else (
  echo.
  echo Tous les tests executes ont reussi.
)
pause
