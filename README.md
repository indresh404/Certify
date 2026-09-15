# Offline Certificate Generator v2

A fast, fully offline desktop application built with Python (CustomTkinter and Pillow) designed to batch-generate high-resolution certificates. It takes a single template image and a data file, visually overlays the names perfectly, and outputs hundreds of certificates in seconds.

## Features

- **100% Offline:** No internet connection required. Complete privacy for your participant data.
- **Excel & CSV Support:** Natively import .xlsx, .xls, and .csv files.
- **Smart Column Selection:** Automatically detects headers and allows you to select which column contains the names.
- **Live Visual Preview:** Drag and drop the text onto the live canvas to perfectly align it. It accurately scales to original-image coordinates.
- **Flawless Text Anchoring:** Uses precise typography ascender/descender metrics to ensure text baseline never bounces between names.
- **Modern UI:** Beautiful Dark Red interface with live generation logs, progress tracking, and ETA metrics.
- **Portable Executable:** Can be bundled into a single .exe file so users don't need Python installed.

## Quick Setup (Windows)

The absolute easiest way to start using the app is via the provided batch scripts:

1. Double click **setup.bat**
   *(This automatically creates a virtual environment, installs the requirements, and starts the application.)*

## Manual Installation

`ash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
`

## How to Build the Standalone .exe

Double click **uild_exe.bat**. 
PyInstaller will automatically bundle the application, fonts, themes, and dependencies into a single standalone .exe located in the dist\CertificateGenerator folder.

## Usage Guide

1. **Template:** Upload your empty certificate template (.png or .jpg).
2. **Data:** Upload your Excel or CSV file.
3. **Column:** Use the dropdown to select the column containing participant names.
4. **Style:** Select the font style, color, size, and alignment.
5. **Positioning:** Click and drag the text on the Live Preview window to place it exactly where you want it.
6. **Generate:** Select an empty output folder and hit Generate!

## Technical Details

- **Language:** Python 3.11+
- **GUI:** CustomTkinter
- **Image Processing:** Pillow (PIL)
- **Data Parsing:** openpyxl (Excel), standard csv module

## License
MIT License
