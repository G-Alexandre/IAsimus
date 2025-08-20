@echo off
chcp 65001 >NUL
setlocal

REM Caminho da pasta deste .bat
cd /d "%~dp0"

REM (opcional) ativar venv se existir
if exist ".venv\Scripts\python.exe" (
  set "PY=.\.venv\Scripts\python.exe"
) else (
  set "PY=python"
)

set PYTHONUTF8=1

%PY% run_wiki_update.py
set ERR=%ERRORLEVEL%

echo.
echo Execucao finalizada com codigo %ERR%.
exit /b %ERR%
