import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pathlib import Path
import os
from PIL import Image
import queue
import time
from threading import Event

from app.core.state import AppState
from app.data.data_reader import load_data, extract_names, DataError
from app.ui.preview_canvas import PreviewCanvas
from app.ui.settings_panel import SettingsPanel, resource_path
from app.ui.progress_dialog import CompletionDialog
from PIL import ImageSequence, ImageTk
from app.core.generator import GeneratorThread

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Certificate Generator")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        self.app_state = AppState()
        
        # UI Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Settings)
        self.settings_panel = SettingsPanel(
            self, 
            state=self.app_state, 
            on_change_callback=self.refresh_preview,
            on_action_callback=self.handle_action,
            width=300
        )
        self.settings_panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Right Panel (Tabs)
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.tabview.add("Preview")
        self.tabview.add("Generation")
        self.tabview.add("About")
        
        self.preview_tab = self.tabview.tab("Preview")
        self.preview_tab.grid_columnconfigure(0, weight=1)
        self.preview_tab.grid_rowconfigure(1, weight=1)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(self.preview_tab, fg_color="transparent")
        zoom_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(zoom_frame, text="LIVE PREVIEW").pack(side="left")
        
        ctk.CTkButton(zoom_frame, text="Fit", width=50, command=lambda: self.canvas.set_zoom("fit")).pack(side="right", padx=2)
        ctk.CTkButton(zoom_frame, text="-", width=30, command=lambda: self.canvas.set_zoom("step", -0.1)).pack(side="right", padx=2)
        ctk.CTkButton(zoom_frame, text="+", width=30, command=lambda: self.canvas.set_zoom("step", 0.1)).pack(side="right", padx=2)
        
        # Canvas
        self.canvas = PreviewCanvas(self.preview_tab, state=self.app_state, on_change_callback=self.refresh_preview, bg="gray15")
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Generation Tab Setup
        self.gen_tab = self.tabview.tab("Generation")
        self.gen_tab.grid_columnconfigure(1, weight=1)
        self.gen_tab.grid_rowconfigure(0, weight=1)
        
        self.gen_left = ctk.CTkFrame(self.gen_tab)
        self.gen_left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.gen_lbl_status = ctk.CTkLabel(self.gen_left, text="Ready to generate.", font=ctk.CTkFont(size=16, weight="bold"))
        self.gen_lbl_status.pack(pady=(20, 10))
        
        self.gen_progress = ctk.CTkProgressBar(self.gen_left, mode="determinate", height=15)
        self.gen_progress.pack(fill="x", padx=30, pady=10)
        self.gen_progress.set(0)
        
        self.gen_lbl_stats = ctk.CTkLabel(self.gen_left, text="Completed: 0 / 0\nFailed: 0\nRemaining: 0", justify="center", font=ctk.CTkFont(size=14))
        self.gen_lbl_stats.pack(pady=10)
        
        self.gen_btn_cancel = ctk.CTkButton(self.gen_left, text="Cancel", command=self.cancel_generation, state="disabled")
        self.gen_btn_cancel.pack(pady=10)
        
        self.gen_right = ctk.CTkFrame(self.gen_tab)
        self.gen_right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(self.gen_right, text="Generation Logs", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.gen_log_textbox = ctk.CTkTextbox(self.gen_right, state="disabled")
        self.gen_log_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # About Tab Setup
        self.about_tab = self.tabview.tab("About")
        self.setup_about_tab()
        
        self.generator_queue = None
        self.generator_thread = None
        self.cancel_event = None

        

    def setup_about_tab(self):
        profile_path = resource_path("assets/image/profile.jpeg")
        if profile_path.exists():
            img = Image.open(profile_path)
            self.profile_img = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
            lbl_img = ctk.CTkLabel(self.about_tab, image=self.profile_img, text="")
            lbl_img.pack(pady=(20, 10))
            
        ctk.CTkLabel(self.about_tab, text="Indresh Suresh", font=ctk.CTkFont(size=24, weight="bold")).pack()
        ctk.CTkLabel(self.about_tab, text="GitHub: @indresh404 (https://github.com/indresh404)").pack(pady=5)
        ctk.CTkLabel(self.about_tab, text="Project: Certify : Certificate Generator").pack(pady=5)
        
        self.gif_label = ctk.CTkLabel(self.about_tab, text="")
        self.gif_label.pack(pady=20)
        
        gif_path = resource_path("assets/image/intro.gif")
        if gif_path.exists():
            self.animate_gif(gif_path)
            
    def animate_gif(self, path):
        img = Image.open(path)
        
        self.gif_frames = []
        self.gif_durations = []
        
        for frame in ImageSequence.Iterator(img):
            self.gif_frames.append(ImageTk.PhotoImage(frame.copy().convert("RGBA")))
            # Get duration, default to 40ms if not present
            duration = frame.info.get('duration', 40)
            if duration < 10:  # Some GIFs report 0 or very low
                duration = 40
            self.gif_durations.append(duration)
        
        def update_frame(idx):
            if not self.winfo_exists(): return
            self.gif_label.configure(image=self.gif_frames[idx])
            self.after(self.gif_durations[idx], update_frame, (idx + 1) % len(self.gif_frames))
            
        if self.gif_frames:
            update_frame(0)
            
    def refresh_preview(self, fit_first=False):
        self.canvas.update_preview(fit_first)
        
    def handle_action(self, action, data=None):
        if action == "load_template":
            self.load_template(Path(data))
        elif action == "load_csv":
            self.load_csv(Path(data))
        elif action == "column_changed":
            self.update_names_from_column()
        elif action == "reset_pos":
            self.app_state.text_x = self.app_state.template_width / 2
            self.app_state.text_y = self.app_state.template_height / 2
            self.refresh_preview()
        elif action == "reset_all":
            # Reset settings logic
            self.app_state.font_size = 48
            self.app_state.text_color = "#000000"
            self.app_state.alignment = "center"
            self.app_state.text_x = self.app_state.template_width / 2
            self.app_state.text_y = self.app_state.template_height / 2
            self.settings_panel.size_var.set("48")
            self.settings_panel.align_var.set("center")
            self.refresh_preview()
        elif action == "generate":
            self.start_generation()
            
    def load_template(self, path: Path):
        try:
            with Image.open(path) as img:
                img.load()
                self.app_state.template_path = path
                self.app_state.template_width = img.width
                self.app_state.template_height = img.height
                
                # Set initial text position to center
                self.app_state.text_x = img.width / 2
                self.app_state.text_y = img.height / 2
                
                self.settings_panel.lbl_tpl_info.configure(
                    text=f"{path.name}\n{img.width} x {img.height}"
                )
                self.refresh_preview(fit_first=True)
        except Exception:
            messagebox.showerror("Error", "Unable to open the selected image. Please choose a valid PNG/JPG image.")
            
    def load_csv(self, path: Path):
        try:
            # We add a small spinner in the main window UI while loading large excel files?
            # CustomTkinter doesn't have a built in spinner, we can use the root window title or just block.
            headers, raw_data = load_data(path)
            self.app_state.csv_path = path
            self.app_state.headers = headers
            self.app_state.raw_data = raw_data
            
            self.settings_panel.col_dropdown.configure(state="normal", values=headers)
            
            # Select "Name" if exists, else first col
            default_col = "Name" if "Name" in headers else (headers[0] if headers else "")
            self.settings_panel.col_var.set(default_col)
            self.app_state.name_column = default_col
            
            self.update_names_from_column()
            
        except DataError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unable to read the data file. {e}")

    def update_names_from_column(self):
        if not self.app_state.raw_data or not self.app_state.name_column:
            return
            
        try:
            names, dups = extract_names(self.app_state.raw_data, self.app_state.name_column)
            self.app_state.names = names
            
            filename = self.app_state.csv_path.name if self.app_state.csv_path else "Data"
            info = f"{filename}\nParticipants: {len(names)}"
            if dups > 0:
                info += f"\nNote: {dups} duplicate names found."
            self.settings_panel.lbl_csv_info.configure(text=info)
            self.refresh_preview()
            
        except DataError as e:
            messagebox.showerror("Error", str(e))
            self.app_state.names = []
            self.settings_panel.lbl_csv_info.configure(text="No valid names found.")
            self.refresh_preview()

    def start_generation(self):
        if not self.app_state.template_path:
            messagebox.showerror("Error", "Please upload a certificate template.")
            return
        if not self.app_state.csv_path or not self.app_state.names:
            messagebox.showerror("Error", "Please upload a CSV file.")
            return
        if not self.app_state.output_folder:
            messagebox.showerror("Error", "Please select an output folder.")
            return
            
        # Check folder writability
        if not os.access(self.app_state.output_folder, os.W_OK):
            messagebox.showerror("Error", "The selected output folder is not writable. Please choose another folder.")
            return
            
        if len(self.app_state.names) > 5000:
            if not messagebox.askyesno("Warning", "You're about to generate 5000+ images. Continue?"):
                return
                
        self.tabview.set("Generation")
        
        self.gen_progress.set(0)
        self.gen_lbl_status.configure(text="Generating certificates...")
        self.gen_btn_cancel.configure(state="normal", text="Cancel")
        self.gen_log_textbox.configure(state="normal")
        self.gen_log_textbox.delete("1.0", "end")
        self.gen_log_textbox.configure(state="disabled")
        
        self.generator_queue = queue.Queue()
        self.cancel_event = Event()
        
        self.generator_thread = GeneratorThread(self.app_state, self.generator_queue, self.cancel_event)
        self.generation_start_time = time.time()
        self.generator_thread.start()
        
        self.after(100, self.poll_queue)
        
    def poll_queue(self):
        if not self.generator_queue: return
        
        try:
            while True:
                msg = self.generator_queue.get_nowait()
                if msg["type"] == "progress":
                    c, f, t = msg["completed"], msg["failed"], msg["total"]
                    if t > 0: self.gen_progress.set(c / t)
                    
                    elapsed = time.time() - self.generation_start_time
                    time_per_item = elapsed / c if c > 0 else 0
                    remaining = time_per_item * (t - c)
                    
                    elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
                    remaining_str = time.strftime('%M:%S', time.gmtime(remaining))
                    
                    stats = f"Completed: {c} / {t}\nFailed: {f}\nRemaining: {t - c}\n\nElapsed: {elapsed_str}\nETA: {remaining_str}"
                    self.gen_lbl_stats.configure(text=stats)
                    
                    self.gen_log_textbox.configure(state="normal")
                    self.gen_log_textbox.insert("end", f"Generated: {msg['current_name']}\n")
                    self.gen_log_textbox.see("end")
                    self.gen_log_textbox.configure(state="disabled")
                    
                elif msg["type"] == "error":
                    messagebox.showerror("Error", msg["message"])
                    self.gen_btn_cancel.configure(state="disabled")
                    return
                elif msg["type"] == "done":
                    c, f, t = msg["completed"], msg["failed"], len(self.app_state.names)
                    self.gen_lbl_status.configure(text="Generation Complete!")
                    self.gen_btn_cancel.configure(state="disabled")
                    
                    elapsed = time.time() - self.generation_start_time
                    elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed))
                    self.gen_lbl_stats.configure(text=f"Completed: {c} / {t}\nFailed: {f}\nRemaining: 0\n\nElapsed: {elapsed_str}\nETA: 00:00")
                    self.gen_log_textbox.configure(state="normal")
                    self.gen_log_textbox.insert("end", f"\nDone in {elapsed_str}. {c} generated, {f} failed.\n")
                    self.gen_log_textbox.see("end")
                    self.gen_log_textbox.configure(state="disabled")
                    
                    CompletionDialog(
                        self, 
                        c, 
                        f, 
                        t, 
                        msg["errors"],
                        self.app_state.output_folder
                    )
                    return
                elif msg["type"] == "cancelled":
                    self.gen_lbl_status.configure(text="Cancelled.")
                    self.gen_btn_cancel.configure(state="disabled")
                    messagebox.showinfo("Cancelled", "Generation cancelled.")
                    return
        except queue.Empty:
            pass
            
        self.after(100, self.poll_queue)
        
    def cancel_generation(self):
        if self.cancel_event:
            self.cancel_event.set()
