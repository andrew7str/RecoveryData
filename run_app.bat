@echo off
REM Simple runner for Windows
REM Create a virtualenv and run recover.py

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%.venv

if not exist "%VENV_DIR%\Scripts\activate.bat" (
  python -m venv "%VENV_DIR%"
  "%VENV_DIR%\Scripts\pip.exe" install --upgrade pip
  if exist "%SCRIPT_DIR%requirements.txt" (
    "%VENV_DIR%\Scripts\pip.exe" install -r "%SCRIPT_DIR%requirements.txt"
  )
)

echo Running recover.py
"%VENV_DIR%\Scripts\python.exe" "%SCRIPT_DIR%recover.py"
