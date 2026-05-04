@echo off
setlocal

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"

cd /d "%PROJECT_DIR%"

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        python -m venv "%VENV_DIR%"
    )
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
python -c "import sys; print('Using Python: ' + sys.executable)"

echo Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo Starting Flask server...
python server\main.py

endlocal
