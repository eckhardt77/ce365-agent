@echo off
REM
REM TechCare Bot - One-Command Installation Script (Windows)
REM
REM Copyright (c) 2026 Carsten Eckhardt / Eckhardt-Marketing
REM Licensed under MIT License
REM
REM Usage: install.bat

echo.
echo ================================================================
echo.
echo    TechCare Bot - Installation
echo.
echo    AI-powered IT-Wartungsassistent
echo.
echo ================================================================
echo.

REM Check Python
echo Pruefe Python-Version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 nicht gefunden!
    echo         Bitte installiere Python 3.9+ von https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% gefunden
echo.

REM Create virtual environment
echo Erstelle Virtual Environment...
if exist venv (
    echo [WARNING] venv existiert bereits, ueberspringe...
) else (
    python -m venv venv
    echo [OK] Virtual Environment erstellt
)
echo.

REM Activate venv
echo Aktiviere Virtual Environment...
call venv\Scripts\activate.bat
echo [OK] Virtual Environment aktiviert
echo.

REM Upgrade pip
echo Aktualisiere pip...
python -m pip install --upgrade pip -q
echo [OK] pip aktualisiert
echo.

REM Install dependencies
echo Installiere Dependencies...
echo (Das kann 2-3 Minuten dauern...)
pip install -r requirements.txt -q
echo [OK] Dependencies installiert
echo.

REM Install Spacy German model
echo Installiere deutsches Sprachmodell (fuer PII Detection)...
python -m spacy download de_core_news_md -q
echo [OK] Sprachmodell installiert
echo.

REM Install TechCare Bot
echo Installiere TechCare Bot...
pip install -e . -q
echo [OK] TechCare Bot installiert
echo.

REM Success
echo ================================================================
echo.
echo    Installation erfolgreich!
echo.
echo ================================================================
echo.
echo Starten mit:
echo.
echo    venv\Scripts\activate.bat  (falls nicht bereits aktiviert)
echo    techcare
echo.
echo Beim ersten Start fuehrt dich ein Setup-Assistent durch die
echo Konfiguration (API Key, etc.).
echo.
echo Dokumentation: docs\INSTALLATION.md
echo Hilfe: https://github.com/your-repo/techcare-bot/issues
echo.
pause
