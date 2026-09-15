import sys
from pathlib import Path
import customtkinter as ctk

from app.ui.main_window import MainWindow

def get_resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.resolve()))
    return base / relative

def main():
    # Set appearance mode and color theme
    ctk.set_appearance_mode("dark")
    
    theme_path = get_resource_path("assets/red_theme.json")
    if theme_path.exists():
        ctk.set_default_color_theme(str(theme_path))
    else:
        ctk.set_default_color_theme("blue")
    
    # Initialize main window
    app = MainWindow()
    
    # Run the application
    app.mainloop()

if __name__ == "__main__":
    main()
