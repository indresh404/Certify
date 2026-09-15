import customtkinter as ctk
import os
import subprocess
import sys
from pathlib import Path

class ProgressDialog(ctk.CTkToplevel):
    def __init__(self, master, cancel_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Generating...")
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Make it modal
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None) # Disable close button
        
        self.cancel_callback = cancel_callback
        
        self.lbl_status = ctk.CTkLabel(self, text="Generating certificates...", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_status.pack(pady=(20, 10))
        
        self.progress = ctk.CTkProgressBar(self, mode="determinate", height=15)
        self.progress.pack(fill="x", padx=30, pady=10)
        self.progress.set(0)
        
        self.lbl_stats = ctk.CTkLabel(self, text="Completed: 0 / 0\nFailed: 0\nRemaining: 0", justify="center", font=ctk.CTkFont(size=14))
        self.lbl_stats.pack(pady=10)
        
        self.btn_cancel = ctk.CTkButton(self, text="Cancel", command=self.on_cancel)
        self.btn_cancel.pack(pady=10)
        
    def update_progress(self, completed, failed, total):
        if total > 0:
            self.progress.set(completed / total)
        remaining = total - completed
        self.lbl_stats.configure(text=f"Completed: {completed} / {total}\nFailed: {failed}\nRemaining: {remaining}")
        
    def on_cancel(self):
        self.btn_cancel.configure(state="disabled", text="Cancelling...")
        self.cancel_callback()
        
class CompletionDialog(ctk.CTkToplevel):
    def __init__(self, master, completed, failed, total, errors, output_folder, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Generation Complete")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        
        self.output_folder = output_folder
        
        status_text = f"Generation Complete!\n{completed} certificates generated successfully."
        if failed > 0:
            status_text = f"Generation Complete\n{completed} successful\n{failed} failed"
            
        ctk.CTkLabel(self, text=status_text).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        if failed > 0:
            # Optionally implement error viewing
            pass
            
        ctk.CTkButton(btn_frame, text="Open Output Folder", command=self.open_folder).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Close", command=self.destroy).pack(side="left", padx=5)
        
    def open_folder(self):
        path = str(self.output_folder)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
