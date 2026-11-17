@echo off
setlocal
cd /d "%~dp0"
set "C5_PY=py -3"
if not "%~1"=="" (
  set C5_PY="%~1"
  goto have_python
)
py -3 --version >nul 2>&1
if errorlevel 1 set "C5_PY=python"
:have_python
%C5_PY% -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11 or newer is required'"
if errorlevel 1 goto fail
if not exist ".venv\Scripts\python.exe" %C5_PY% -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Setup complete. Run C5-Tools.cmd. No USB device was accessed.
pause
exit /b 0
:fail
echo Setup failed. Install Python 3.11 or newer and check the message above.
echo You can also run setup.cmd "C:\path\to\python.exe".
pause
exit /b 1
