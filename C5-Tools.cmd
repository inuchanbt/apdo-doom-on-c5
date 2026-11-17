@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.cmd first. See README.md or README.ja.md.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -X utf8 tools\launcher.py %*
set "C5_RESULT=%ERRORLEVEL%"
pause
exit /b %C5_RESULT%
