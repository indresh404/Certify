import sys
from pathlib import Path
from tkinter import colorchooser, filedialog

import customtkinter as ctk

from app.core.state import AppState


def resource_path(relative: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent))
    return base / relative


class SettingsPanel(ctk.CTkScrollableFrame):
    def __init__(
        self, master, state: AppState, on_change_callback, on_action_callback, **kwargs
    ):
        super().__init__(master, **kwargs)
        self.state = state
        self.on_change = on_change_callback
        self.on_action = on_action_callback

        self.grid_columnconfigure(0, weight=1)

        # ---------------- 1. Template Section ----------------
        self.lbl_template = ctk.CTkLabel(
            self, text="TEMPLATE", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_template.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.btn_upload_tpl = ctk.CTkButton(
            self, text="Upload Template", command=self.upload_template
        )
        self.btn_upload_tpl.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.lbl_tpl_info = ctk.CTkLabel(
            self, text="No template loaded", text_color="gray", justify="left"
        )
        self.lbl_tpl_info.grid(row=2, column=0, sticky="w", padx=10)

        # ---------------- 2. Data Section ----------------
        self.lbl_csv = ctk.CTkLabel(
            self, text="DATA (CSV / Excel)", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_csv.grid(row=3, column=0, sticky="w", padx=10, pady=(20, 0))

        self.btn_upload_csv = ctk.CTkButton(
            self, text="Upload Data File", command=self.upload_csv
        )
        self.btn_upload_csv.grid(row=4, column=0, sticky="ew", padx=10, pady=5)

        self.lbl_csv_info = ctk.CTkLabel(
            self, text="No file loaded", text_color="gray", justify="left"
        )
        self.lbl_csv_info.grid(row=5, column=0, sticky="w", padx=10)

        # Filename Column selection
        filename_frame = ctk.CTkFrame(self, fg_color="transparent")
        filename_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=(8, 2))
        ctk.CTkLabel(filename_frame, text="Filename Column:").pack(side="left")

        self.filename_col_var = ctk.StringVar(value="")
        self.filename_col_dropdown = ctk.CTkOptionMenu(
            filename_frame,
            variable=self.filename_col_var,
            values=["(Upload data first)"],
            command=self.filename_column_changed,
        )
        self.filename_col_dropdown.pack(
            side="right", fill="x", expand=True, padx=(5, 0)
        )
        self.filename_col_dropdown.configure(state="disabled")

        # ---------------- 3. Certificate Fields (Only chosen columns) ----------------
        self.lbl_cols_header = ctk.CTkLabel(
            self, text="CERTIFICATE FIELDS", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_cols_header.grid(row=7, column=0, sticky="w", padx=10, pady=(20, 0))

        # Add Column Row
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.grid(row=8, column=0, sticky="ew", padx=10, pady=(2, 6))
        add_frame.grid_columnconfigure(0, weight=1)

        self.add_col_var = ctk.StringVar(value="")
        self.add_col_dropdown = ctk.CTkOptionMenu(
            add_frame,
            variable=self.add_col_var,
            values=["(Upload data first)"],
        )
        self.add_col_dropdown.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.add_col_dropdown.configure(state="disabled")

        self.btn_add_col = ctk.CTkButton(
            add_frame,
            text="+ Add Field",
            width=85,
            command=self.add_field_clicked,
        )
        self.btn_add_col.grid(row=0, column=1, sticky="e")
        self.btn_add_col.configure(state="disabled")

        # Fields List Container
        self.columns_list_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"))
        self.columns_list_frame.grid(row=9, column=0, sticky="ew", padx=10, pady=2)
        self.columns_list_frame.grid_columnconfigure(0, weight=1)

        # ---------------- 4. Field Settings ----------------
        self.lbl_settings = ctk.CTkLabel(
            self, text="FIELD SETTINGS", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_settings.grid(row=10, column=0, sticky="w", padx=10, pady=(20, 0))

        # Active Field Selector / Status
        active_frame = ctk.CTkFrame(self, fg_color="transparent")
        active_frame.grid(row=11, column=0, sticky="ew", padx=10, pady=5)
        active_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(active_frame, text="Active Field:").grid(
            row=0, column=0, sticky="w"
        )
        self.active_field_var = ctk.StringVar(value="")
        self.active_field_dropdown = ctk.CTkOptionMenu(
            active_frame,
            variable=self.active_field_var,
            values=["(No field)"],
            command=self.active_field_changed,
        )
        self.active_field_dropdown.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        # Font settings
        font_frame = ctk.CTkFrame(self, fg_color="transparent")
        font_frame.grid(row=12, column=0, sticky="ew", padx=10, pady=5)
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
        size_frame.grid(row=13, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(size_frame, text="Font Size").grid(row=0, column=0, sticky="w")

        self.size_var = ctk.StringVar(value="48")
        self.entry_size = ctk.CTkEntry(
            size_frame, textvariable=self.size_var, width=50
        )
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
        color_align_frame.grid(row=14, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(color_align_frame, text="Color").grid(row=0, column=0, sticky="w")
        self.btn_color = ctk.CTkButton(
            color_align_frame,
            text="■ #000000",
            width=90,
            command=self.pick_color,
        )
        self.btn_color.grid(row=0, column=1, padx=(10, 10))

        ctk.CTkLabel(color_align_frame, text="Align").grid(row=0, column=2, sticky="w")
        self.align_var = ctk.StringVar(value="center")
        self.align_dropdown = ctk.CTkOptionMenu(
            color_align_frame,
            variable=self.align_var,
            values=["left", "center", "right"],
            width=80,
            command=self.align_changed,
        )
        self.align_dropdown.grid(row=0, column=3, padx=(5, 0))

        # Auto-fit
        self.autofit_var = ctk.BooleanVar(value=False)
        self.chk_autofit = ctk.CTkCheckBox(
            self,
            text="Auto-fit to width",
            variable=self.autofit_var,
            command=self.autofit_changed,
        )
        self.chk_autofit.grid(row=15, column=0, sticky="w", padx=10, pady=5)

        # Position Coordinates (X, Y)
        pos_frame = ctk.CTkFrame(self, fg_color="transparent")
        pos_frame.grid(row=16, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(pos_frame, text="X:").grid(row=0, column=0, sticky="w")
        self.x_var = ctk.StringVar(value="0")
        self.entry_x = ctk.CTkEntry(pos_frame, textvariable=self.x_var, width=60)
        self.entry_x.grid(row=0, column=1, padx=(5, 10))
        self.entry_x.bind("<Return>", self.coord_changed)
        self.entry_x.bind("<FocusOut>", self.coord_changed)

        ctk.CTkLabel(pos_frame, text="Y:").grid(row=0, column=2, sticky="w")
        self.y_var = ctk.StringVar(value="0")
        self.entry_y = ctk.CTkEntry(pos_frame, textvariable=self.y_var, width=60)
        self.entry_y.grid(row=0, column=3, padx=(5, 10))
        self.entry_y.bind("<Return>", self.coord_changed)
        self.entry_y.bind("<FocusOut>", self.coord_changed)

        # Center / Alignment Buttons
        align_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        align_btn_frame.grid(row=17, column=0, sticky="ew", padx=10, pady=5)
        align_btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            align_btn_frame,
            text="Center Horizontally",
            command=self.center_field_x,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(
            align_btn_frame,
            text="Center Vertically",
            command=self.center_field_y,
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Reset buttons
        reset_frame = ctk.CTkFrame(self, fg_color="transparent")
        reset_frame.grid(row=18, column=0, sticky="ew", padx=10, pady=5)
        reset_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            reset_frame,
            text="Reset Field Pos",
            command=lambda: self.on_action("reset_pos"),
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(
            reset_frame,
            text="Reset All Fields",
            command=lambda: self.on_action("reset_all"),
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # ---------------- 5. Output Section ----------------
        self.lbl_output = ctk.CTkLabel(
            self, text="OUTPUT", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_output.grid(row=19, column=0, sticky="w", padx=10, pady=(20, 0))

        self.btn_output = ctk.CTkButton(
            self, text="Select Output Folder", command=self.select_output
        )
        self.btn_output.grid(row=20, column=0, sticky="ew", padx=10, pady=5)

        self.lbl_out_info = ctk.CTkLabel(
            self, text="No folder selected", text_color="gray", justify="left"
        )
        self.lbl_out_info.grid(row=21, column=0, sticky="w", padx=10)

        # ---------------- 6. Generate Button ----------------
        self.btn_generate = ctk.CTkButton(
            self,
            text="GENERATE CERTIFICATES",
            height=42,
            font=ctk.CTkFont(weight="bold", size=14),
            command=lambda: self.on_action("generate"),
        )
        self.btn_generate.grid(row=22, column=0, sticky="ew", padx=10, pady=20)

        self.refresh_font_list()
        self.update_fields_list()

    def refresh_font_list(self):
        font_dir = resource_path("assets/fonts")
        if font_dir.exists():
            fonts = [f.stem for f in font_dir.glob("*.ttf")]
            if fonts:
                self.font_dropdown.configure(values=fonts)
                if (
                    self.state.active_field
                    and not self.state.active_field.font_path
                ):
                    self.font_var.set(fonts[0])
                    self.state.active_field.font_name = fonts[0]
                    self.state.active_field.font_path = font_dir / f"{fonts[0]}.ttf"

    def update_fields_list(self):
        # Update Add Column dropdown with all available CSV headers
        if self.state.headers:
            self.add_col_dropdown.configure(values=self.state.headers, state="normal")
            # Set default add dropdown selection to next unused header if possible
            existing_names = {f.column_name for f in self.state.fields}
            unused = [h for h in self.state.headers if h not in existing_names]
            default_choice = unused[0] if unused else self.state.headers[0]
            self.add_col_var.set(default_choice)
            self.btn_add_col.configure(state="normal")

            # Filename dropdown can choose from any CSV column
            self.filename_col_dropdown.configure(
                values=self.state.headers, state="normal"
            )
            if (
                self.state.filename_column
                and self.state.filename_column in self.state.headers
            ):
                self.filename_col_var.set(self.state.filename_column)
            else:
                self.filename_col_var.set(self.state.headers[0])
                self.state.filename_column = self.state.headers[0]
        else:
            self.add_col_dropdown.configure(
                values=["(Upload data first)"], state="disabled"
            )
            self.add_col_var.set("(Upload data first)")
            self.btn_add_col.configure(state="disabled")
            self.filename_col_dropdown.configure(
                values=["(Upload data first)"], state="disabled"
            )

        # Clear existing active field rows
        for widget in self.columns_list_frame.winfo_children():
            widget.destroy()

        if not self.state.fields:
            lbl_empty = ctk.CTkLabel(
                self.columns_list_frame,
                text="No fields on certificate.\nSelect a column above and click '+ Add Field'.",
                text_color="gray",
                font=ctk.CTkFont(size=11),
                justify="center",
            )
            lbl_empty.pack(padx=10, pady=12)
            self.active_field_dropdown.configure(
                values=["(No field)"], state="disabled"
            )
            self.active_field_var.set("(No field)")
            return

        col_names = [f.column_name for f in self.state.fields]
        self.active_field_dropdown.configure(values=col_names, state="normal")

        # Build clean list of fields added to certificate
        for idx, field_cfg in enumerate(self.state.fields):
            is_active = idx == self.state.active_field_index
            row_bg = ("#DBEAFE", "#1E3A5F") if is_active else "transparent"
            row_frame = ctk.CTkFrame(self.columns_list_frame, fg_color=row_bg, corner_radius=6)
            row_frame.pack(fill="x", padx=4, pady=2)

            lbl_text = f"• {field_cfg.column_name}"
            lbl = ctk.CTkLabel(
                row_frame,
                text=lbl_text,
                font=ctk.CTkFont(weight="bold" if is_active else "normal", size=12),
                text_color=("#1D4ED8", "#93C5FD") if is_active else ("black", "white"),
            )
            lbl.pack(side="left", padx=8, pady=4)

            btn_remove = ctk.CTkButton(
                row_frame,
                text="✕",
                width=24,
                height=22,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#991B1B", "#FCA5A5"),
                hover_color=("#FCA5A5", "#991B1B"),
                command=lambda i=idx: self.remove_field_clicked(i),
            )
            btn_remove.pack(side="right", padx=(2, 6), pady=3)

            btn_edit = ctk.CTkButton(
                row_frame,
                text="Edit",
                width=42,
                height=22,
                font=ctk.CTkFont(size=11),
                command=lambda i=idx: self.select_active_field_by_index(i),
            )
            btn_edit.pack(side="right", padx=2, pady=3)

        # Sync active field controls
        if self.state.active_field_index >= len(self.state.fields):
            self.state.active_field_index = max(0, len(self.state.fields) - 1)
        self.sync_controls_from_active_field()

    def add_field_clicked(self):
        col = self.add_col_var.get()
        if not col or col == "(Upload data first)":
            return

        font_name = self.font_var.get() or "OpenSans-Regular"
        font_path = resource_path("assets/fonts") / f"{font_name}.ttf"
        self.state.add_field(
            column_name=col,
            font_name=font_name,
            font_path=font_path if font_path.exists() else None,
        )
        self.update_fields_list()
        self.on_change()

    def remove_field_clicked(self, index: int):
        self.state.remove_field(index)
        self.update_fields_list()
        self.on_change()

    def select_active_field_by_index(self, index: int):
        if 0 <= index < len(self.state.fields):
            self.state.active_field_index = index
            self.update_fields_list()
            self.sync_controls_from_active_field()
            self.on_change()

    def sync_controls_from_active_field(self):
        active = self.state.active_field
        if not active:
            return

        self.active_field_var.set(active.column_name)
        self.font_var.set(active.font_name)
        self.size_var.set(str(active.font_size))
        self.align_var.set(active.alignment)
        self.autofit_var.set(active.auto_fit)
        self.x_var.set(f"{active.text_x:.1f}")
        self.y_var.set(f"{active.text_y:.1f}")
        self.btn_color.configure(text=f"■ {active.text_color}")

    def update_coords_from_state(self):
        active = self.state.active_field
        if active:
            self.x_var.set(f"{active.text_x:.1f}")
            self.y_var.set(f"{active.text_y:.1f}")

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

    def filename_column_changed(self, choice):
        self.state.filename_column = choice

    def active_field_changed(self, choice):
        for idx, f in enumerate(self.state.fields):
            if f.column_name == choice:
                self.state.active_field_index = idx
                self.update_fields_list()
                self.sync_controls_from_active_field()
                self.on_change()
                break

    def font_changed(self, choice):
        active = self.state.active_field
        if active:
            active.font_name = choice
            active.font_path = resource_path("assets/fonts") / f"{choice}.ttf"
            self.on_change()

    def browse_font(self):
        path = filedialog.askopenfilename(filetypes=[("Fonts", "*.ttf *.otf")])
        if path:
            active = self.state.active_field
            if active:
                active.font_path = Path(path)
                active.font_name = Path(path).stem
                self.font_var.set(active.font_name)
                self.on_change()

    def size_changed(self, event=None):
        try:
            val = int(self.size_var.get())
            if val > 0:
                active = self.state.active_field
                if active:
                    active.font_size = val
                    self.on_change()
        except ValueError:
            active = self.state.active_field
            if active:
                self.size_var.set(str(active.font_size))

    def adjust_size(self, delta):
        active = self.state.active_field
        if active:
            active.font_size = max(1, active.font_size + delta)
            self.size_var.set(str(active.font_size))
            self.on_change()

    def pick_color(self):
        active = self.state.active_field
        if not active:
            return
        color = colorchooser.askcolor(initialcolor=active.text_color)[1]
        if color:
            active.text_color = color
            self.btn_color.configure(text=f"■ {color}")
            self.on_change()

    def align_changed(self, choice):
        active = self.state.active_field
        if active:
            active.alignment = choice
            self.on_change()

    def autofit_changed(self):
        active = self.state.active_field
        if active:
            active.auto_fit = self.autofit_var.get()
            self.on_change()

    def coord_changed(self, event=None):
        active = self.state.active_field
        if not active:
            return
        try:
            x_val = float(self.x_var.get())
            y_val = float(self.y_var.get())
            active.text_x = x_val
            active.text_y = y_val
            self.on_change()
        except ValueError:
            self.update_coords_from_state()

    def center_field_x(self):
        active = self.state.active_field
        if active and self.state.template_width > 0:
            active.text_x = self.state.template_width / 2.0
            self.x_var.set(f"{active.text_x:.1f}")
            self.on_change()

    def center_field_y(self):
        active = self.state.active_field
        if active and self.state.template_height > 0:
            active.text_y = self.state.template_height / 2.0
            self.y_var.set(f"{active.text_y:.1f}")
            self.on_change()

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.state.output_folder = Path(path)
            self.lbl_out_info.configure(text=str(self.state.output_folder))


