import sys
from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk

from app.core.state import AppState


def resource_path(relative: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent))
    return base / relative


class SettingsPanel(ctk.CTkFrame):
    def __init__(
        self, master, state: AppState, on_change_callback, on_action_callback, **kwargs
    ):
        super().__init__(master, **kwargs)
        self.state = state
        self.on_change = on_change_callback
        self.on_action = on_action_callback

        self.grid_columnconfigure(0, weight=1)

        # Template Section
        self.lbl_template = ctk.CTkLabel(
            self, text="TEMPLATE", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_template.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.btn_upload_tpl = ctk.CTkButton(
            self, text="Upload Template", command=self.upload_template
        )
        self.btn_upload_tpl.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.lbl_tpl_info = ctk.CTkLabel(self, text="No template loaded")
        self.lbl_tpl_info.grid(row=2, column=0, sticky="w", padx=10)

        # Data Section
        self.lbl_csv = ctk.CTkLabel(
            self, text="DATA (CSV / Excel)", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_csv.grid(row=3, column=0, sticky="w", padx=10, pady=(20, 0))

        self.btn_upload_csv = ctk.CTkButton(
            self, text="Upload Data File", command=self.upload_csv
        )
        self.btn_upload_csv.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

        # Column selection
        col_frame = ctk.CTkFrame(self, fg_color="transparent")
        col_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=2)
        ctk.CTkLabel(col_frame, text="Name Column:").pack(side="left")

        self.col_var = ctk.StringVar(value="")
        self.col_dropdown = ctk.CTkOptionMenu(
            col_frame, variable=self.col_var, values=[""], command=self.column_changed
        )
        self.col_dropdown.pack(side="right", fill="x", expand=True, padx=(5, 0))
        self.col_dropdown.configure(state="disabled")

        self.lbl_csv_info = ctk.CTkLabel(self, text="No file loaded")
        self.lbl_csv_info.grid(row=6, column=0, sticky="w", padx=10)

        # Settings Section
        self.lbl_settings = ctk.CTkLabel(
            self, text="NAME SETTINGS", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_settings.grid(row=7, column=0, sticky="w", padx=10, pady=(20, 0))

        # Font settings
        font_frame = ctk.CTkFrame(self, fg_color="transparent")
        font_frame.grid(row=8, column=0, sticky="ew", padx=10, pady=5)
        font_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(font_frame, text="Font").grid(row=0, column=0, sticky="w")
        self.font_var = ctk.StringVar(value="OpenSans-Regular")
        self.font_dropdown = ctk.CTkOptionMenu(
            font_frame, variable=self.font_var, command=self.font_changed
        )
        self.font_dropdown.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        self.btn_browse_font = ctk.CTkButton(
            font_frame, text="Browse...", width=60, command=self.browse_font
        )
        self.btn_browse_font.grid(row=0, column=2, padx=(5, 0))

        # Size settings
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.grid(row=9, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(size_frame, text="Font Size").grid(row=0, column=0, sticky="w")

        self.size_var = ctk.StringVar(value=str(self.state.font_size))
        self.entry_size = ctk.CTkEntry(size_frame, textvariable=self.size_var, width=50)
        self.entry_size.grid(row=0, column=1, padx=(10, 5))
        self.entry_size.bind("<Return>", self.size_changed)
        self.entry_size.bind("<FocusOut>", self.size_changed)

        ctk.CTkButton(
            size_frame, text="-", width=30, command=lambda: self.adjust_size(-1)
        ).grid(row=0, column=2, padx=2)
        ctk.CTkButton(
            size_frame, text="+", width=30, command=lambda: self.adjust_size(1)
        ).grid(row=0, column=3, padx=2)

        # Color & Alignment
        color_align_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_align_frame.grid(row=10, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(color_align_frame, text="Color").grid(row=0, column=0, sticky="w")
        self.btn_color = ctk.CTkButton(
            color_align_frame, text="■ Select", width=80, command=self.pick_color
        )
        self.btn_color.grid(row=0, column=1, padx=(10, 10))

        ctk.CTkLabel(color_align_frame, text="Align").grid(row=0, column=2, sticky="w")
        self.align_var = ctk.StringVar(value=self.state.alignment)
        self.align_dropdown = ctk.CTkOptionMenu(
            color_align_frame,
            variable=self.align_var,
            values=["left", "center", "right"],
            width=80,
            command=self.align_changed,
        )
        self.align_dropdown.grid(row=0, column=3, padx=(5, 0))

        # Auto-fit
        self.autofit_var = ctk.BooleanVar(value=self.state.auto_fit)
        self.chk_autofit = ctk.CTkCheckBox(
            self,
            text="Auto-fit to width",
            variable=self.autofit_var,
            command=self.autofit_changed,
        )
        self.chk_autofit.grid(row=11, column=0, sticky="w", padx=10, pady=5)

        # Reset buttons
        reset_frame = ctk.CTkFrame(self, fg_color="transparent")
        reset_frame.grid(row=12, column=0, sticky="ew", padx=10, pady=10)
        reset_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            reset_frame, text="Reset Pos", command=lambda: self.on_action("reset_pos")
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(
            reset_frame, text="Reset All", command=lambda: self.on_action("reset_all")
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Output
        self.lbl_output = ctk.CTkLabel(
            self, text="OUTPUT", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_output.grid(row=13, column=0, sticky="w", padx=10, pady=(20, 0))

        self.btn_output = ctk.CTkButton(
            self, text="Select Folder", command=self.select_output
        )
        self.btn_output.grid(row=14, column=0, sticky="ew", padx=10, pady=5)

        self.lbl_out_info = ctk.CTkLabel(self, text="No folder selected")
        self.lbl_out_info.grid(row=15, column=0, sticky="w", padx=10)

        # Generate
        self.btn_generate = ctk.CTkButton(
            self,
            text="GENERATE",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            command=lambda: self.on_action("generate"),
        )
        self.btn_generate.grid(row=16, column=0, sticky="ew", padx=10, pady=20)

        self.refresh_font_list()

    def refresh_font_list(self):
        font_dir = resource_path("assets/fonts")
        if font_dir.exists():
            fonts = [f.stem for f in font_dir.glob("*.ttf")]
            if fonts:
                self.font_dropdown.configure(values=fonts)
                if not self.state.font_path:
                    self.font_var.set(fonts[0])
                    self.state.font_name = fonts[0]
                    self.state.font_path = font_dir / f"{fonts[0]}.ttf"

    def upload_template(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")]
        )
        if path:
            self.on_action("load_template", path)

    def upload_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("Data Files", "*.csv *.xlsx *.xls")]
        )
        if path:
            self.on_action("load_csv", path)

    def column_changed(self, choice):
        self.state.name_column = choice
        self.on_action("column_changed")

    def font_changed(self, choice):
        self.state.font_name = choice
        self.state.font_path = resource_path("assets/fonts") / f"{choice}.ttf"
        self.on_change()

    def browse_font(self):
        path = filedialog.askopenfilename(filetypes=[("Fonts", "*.ttf *.otf")])
        if path:
            self.state.font_path = Path(path)
            self.state.font_name = Path(path).stem
            self.font_var.set(self.state.font_name)
            self.on_change()

    def size_changed(self, event=None):
        try:
            val = int(self.size_var.get())
            if val > 0:
                self.state.font_size = val
                self.on_change()
        except ValueError:
            self.size_var.set(str(self.state.font_size))

    def adjust_size(self, delta):
        self.state.font_size = max(1, self.state.font_size + delta)
        self.size_var.set(str(self.state.font_size))
        self.on_change()

    def pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.state.text_color)[1]
        if color:
            self.state.text_color = color
            self.on_change()

    def align_changed(self, choice):
        self.state.alignment = choice
        self.on_change()

    def autofit_changed(self):
        self.state.auto_fit = self.autofit_var.get()
        self.on_change()

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.state.output_folder = Path(path)
            self.lbl_out_info.configure(text=str(self.state.output_folder))
