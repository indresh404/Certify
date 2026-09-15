@echo off
echo Setting up Certificate Generator...
echo.

IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Setup Complete! Starting application...
python main.py
