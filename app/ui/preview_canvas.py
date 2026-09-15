import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk

from app.core.coordinates import original_to_preview, preview_to_original
from app.core.renderer import auto_fit_font_size, calculate_text_position, measure_text
from app.core.state import AppState


class PreviewCanvas(ctk.CTkCanvas):
    def __init__(self, master, state: AppState, on_change_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.state = state
        self.on_change = on_change_callback

        self.bind("<Configure>", self.on_resize)

        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)

        # Debounce resize
        self.resize_after_id = None

        self.photo_image = None
        self.bg_image_id = None
        self.text_id = None
        self.bbox_id = None
        self.h_guide = None
        self.v_guide = None

        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.start_text_x = 0.0
        self.start_text_y = 0.0

    def on_resize(self, event):
        if self.resize_after_id:
            self.after_cancel(self.resize_after_id)
        self.resize_after_id = self.after(100, self.update_preview)

    def set_zoom(self, mode: str, step: float = 0.0):
        if mode == "fit":
            self.fit_to_canvas()
        else:
            self.state.preview_scale = max(
                0.1, min(10.0, self.state.preview_scale + step)
            )

        self.update_preview()

    def fit_to_canvas(self):
        if not self.state.template_path or self.state.template_width == 0:
            return

        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()

        if canvas_w <= 1 or canvas_h <= 1:
            return  # not fully rendered yet

        scale_w = canvas_w / self.state.template_width
        scale_h = canvas_h / self.state.template_height

        self.state.preview_scale = min(scale_w, scale_h) * 0.95  # 5% padding

        # Center offset
        preview_w = self.state.template_width * self.state.preview_scale
        preview_h = self.state.template_height * self.state.preview_scale

        offset_x = (canvas_w - preview_w) / 2.0
        offset_y = (canvas_h - preview_h) / 2.0

        self.state.preview_offset = (offset_x, offset_y)

    def update_preview(self, fit_first=False):
        if not self.state.template_path:
            self.delete("all")
            self.create_text(
                self.winfo_width() / 2,
                self.winfo_height() / 2,
                text="Upload a template to begin",
                fill="gray",
            )
            return

        if fit_first:
            self.fit_to_canvas()

        self.delete("all")

        scale = self.state.preview_scale
        offset_x, offset_y = self.state.preview_offset

        target_w = int(self.state.template_width * scale)
        target_h = int(self.state.template_height * scale)

        if target_w <= 0 or target_h <= 0:
            return

        # Re-open or use cached image to render preview
        try:
            with Image.open(self.state.template_path) as img:
                img.load()
                preview_img = img.resize((target_w, target_h), Image.LANCZOS)
                self.photo_image = ImageTk.PhotoImage(preview_img)
                self.bg_image_id = self.create_image(
                    offset_x, offset_y, anchor="nw", image=self.photo_image
                )
        except Exception as e:  # noqa: BLE001
            print(f"Error loading preview: {e}")
            return

        self.draw_text_overlay()

    def draw_text_overlay(self):
        # We draw text using tkinter canvas so it's live/vector-like
        # We calculate the position and font size

        # delete old text overlay
        if self.text_id:
            self.delete(self.text_id)
        if self.bbox_id:
            self.delete(self.bbox_id)
        if self.h_guide:
            self.delete(self.h_guide)
        if self.v_guide:
            self.delete(self.v_guide)

        preview_name = "Sample Name"
        if self.state.names:
            preview_name = self.state.names[0]

        if not preview_name:
            return

        scale = self.state.preview_scale
        offset = self.state.preview_offset

        # Calculate final size (simulating auto-fit if necessary)
        final_size = self.state.font_size
        font_path = str(self.state.font_path) if self.state.font_path else ""

        safe_margin_px = self.state.template_width * self.state.safe_margin_pct
        max_width = self.state.template_width - (2 * safe_margin_px)

        if self.state.auto_fit and font_path:
            try:
                # We need a dummy image draw to measure
                dummy_img = Image.new("RGB", (1, 1))
                draw = ImageDraw.Draw(dummy_img)
                final_size = auto_fit_font_size(
                    draw, preview_name, font_path, self.state.font_size, max_width
                )
            except Exception:  # noqa: BLE001, S110
                pass

        # Convert original coordinates to preview coordinates
        px, py = original_to_preview(
            self.state.text_x, self.state.text_y, scale, offset
        )

        # Set up font for tkinter
        # Tkinter font loading from path is notoriously hard cross-platform.
        # For the live preview, we use a generic approximation if path is not supported by tk
        # However, custom fonts are requested. We can draw the text onto a transparent PIL image
        # and display it on the canvas for 100% fidelity.

        # Render text via PIL for perfect accuracy
        try:
            font = (
                ImageFont.truetype(font_path, int(final_size * scale))
                if font_path
                else ImageFont.load_default()
            )
            dummy_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
            draw = ImageDraw.Draw(dummy_img)
            bbox = measure_text(draw, preview_name, font)

            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]

            # The "px, py" anchor is the original-space text_x, text_y scaled.
            # calculate_text_position gives us the top-left of the text in original space
            # Let's do calculation in original space then scale, or scale then calculate.
            # It's better to scale the dimensions.

            draw_ox, draw_oy = calculate_text_position(
                (bbox[0] / scale, bbox[1] / scale, bbox[2] / scale, bbox[3] / scale),
                self.state.text_x,
                self.state.text_y,
                self.state.alignment,
            )

            # Now convert draw_ox, draw_oy to preview coords
            draw_px, draw_py = original_to_preview(draw_ox, draw_oy, scale, offset)

            # Create a transparent image for the text
            text_img = Image.new("RGBA", (int(w) + 10, int(h) + 10), (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_img)
            # Offset slightly to handle padding
            text_draw.text(
                (-bbox[0] + 5, -bbox[1] + 5),
                preview_name,
                font=font,
                fill=self.state.text_color,
            )

            self.tk_text_img = ImageTk.PhotoImage(text_img)
            self.text_id = self.create_image(
                draw_px - 5, draw_py - 5, anchor="nw", image=self.tk_text_img
            )

            # Draw bounding box
            self.bbox_id = self.create_rectangle(
                draw_px, draw_py, draw_px + w, draw_py + h, dash=(4, 4), outline="blue"
            )

            # Guide lines (only when dragging)
            if self.is_dragging:
                canvas_center_x = self.winfo_width() / 2
                canvas_center_y = self.winfo_height() / 2

                # Check if close to center
                if abs(px - canvas_center_x) < 10:
                    self.v_guide = self.create_line(
                        canvas_center_x,
                        0,
                        canvas_center_x,
                        self.winfo_height(),
                        fill="red",
                        dash=(2, 2),
                    )
                if abs(py - canvas_center_y) < 10:
                    self.h_guide = self.create_line(
                        0,
                        canvas_center_y,
                        self.winfo_width(),
                        canvas_center_y,
                        fill="red",
                        dash=(2, 2),
                    )

        except Exception as e:  # noqa: BLE001
            print(f"Error drawing text preview: {e}")

    def on_press(self, event):
        if not self.state.template_path:
            return
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.start_text_x = self.state.text_x
        self.start_text_y = self.state.text_y

    def on_drag(self, event):
        if not self.is_dragging:
            return

        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        # Convert delta to original space
        scale = self.state.preview_scale
        if scale == 0:
            return

        ox_delta = dx / scale
        oy_delta = dy / scale

        # Update state
        self.state.text_x = self.start_text_x + ox_delta
        self.state.text_y = self.start_text_y + oy_delta

        # Clamp to canvas
        px, py = original_to_preview(
            self.state.text_x, self.state.text_y, scale, self.state.preview_offset
        )

        canvas_center_x = self.winfo_width() / 2
        canvas_center_y = self.winfo_height() / 2

        # Snapping logic
        if abs(px - canvas_center_x) < 10:
            px = canvas_center_x
        if abs(py - canvas_center_y) < 10:
            py = canvas_center_y

        # Write back snapped coordinates
        self.state.text_x, self.state.text_y = preview_to_original(
            px, py, scale, self.state.preview_offset
        )

        self.draw_text_overlay()

    def on_release(self, event):
        self.is_dragging = False
        self.draw_text_overlay()
        if self.on_change:
            self.on_change()
