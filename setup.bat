@echo off
setlocal enabledelayedexpansion

echo =================================================================
echo  Brain Map AI - One-Click Installer ^& Dependency Setup
echo =================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.12 (64-bit) and check "Add Python to PATH".
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
) else (
    echo [INFO] Virtual environment 'venv' already exists. Skipping creation.
)

:: Upgrade pip and install dependencies
echo.
echo [INFO] Activating virtual environment and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
if !errorlevel! neq 0 (
    echo [WARNING] Failed to upgrade pip. Continuing...
)

echo.
echo [INFO] Installing required packages from requirements.txt...
echo This might take a few minutes depending on your internet connection...
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Dependency installation failed. Please check your internet connection.
    pause
    exit /b 1
)
echo [SUCCESS] All requirements.txt dependencies installed.

:: Install SpaCy English Model
echo.
echo [INFO] Downloading and installing spaCy English language model (en_core_web_sm)...
python -m spacy download en_core_web_sm
if !errorlevel! neq 0 (
    echo [ERROR] Failed to download spaCy English model.
    pause
    exit /b 1
)
echo [SUCCESS] spaCy model configured.

echo.
echo =================================================================
echo  Brain Map AI Setup Complete!
echo =================================================================
echo.
echo  To run the application, double-click or run: run_app.bat
echo.
pause
exit /b 0
