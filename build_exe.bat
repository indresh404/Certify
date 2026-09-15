@echo off
echo Building EXE...
echo.

call venv\Scripts\activate
pip install pyinstaller

echo Packaging application...
pyinstaller --noconfirm --windowed --name CertificateGenerator --collect-all customtkinter --add-data "assets;assets" main.py

echo.
echo Build Complete! The executable is located in the dist\CertificateGenerator folder.
pause
