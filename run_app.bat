@echo off
echo =================================================================
echo  Launching Smart Notes to Mind Map AI...
echo =================================================================
echo.

if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run 'setup.bat' first to install all dependencies.
    pause
    exit /b 1
)

:: Run streamlit using the virtual environment
call venv\Scripts\activate.bat
streamlit run app.py
pause
