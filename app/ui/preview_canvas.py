import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk

from app.core.coordinates import original_to_preview, preview_to_original
from app.core.renderer import auto_fit_font_size, get_text_anchor, measure_text_anchored
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
        if getattr(self, "text_item", None):
            self.delete(self.text_item)
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
        offset_x, offset_y = self.state.preview_offset

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

        try:
            font = (
                ImageFont.truetype(font_path, int(final_size))
                if font_path
                else ImageFont.load_default()
            )
            dummy_img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
            draw = ImageDraw.Draw(dummy_img)

            # Calculate position using anchored text
            bbox = measure_text_anchored(
                draw,
                preview_name,
                font,
                self.state.text_x,
                self.state.text_y,
                self.state.alignment,
            )

            # Convert bbox to preview coordinates
            left, top, right, bottom = bbox
            px_left, py_top = original_to_preview(
                left, top, scale, (offset_x, offset_y)
            )
            px_right, py_bottom = original_to_preview(
                right, bottom, scale, (offset_x, offset_y)
            )

            p_width = max(1, int(px_right - px_left))
            p_height = max(1, int(py_bottom - py_top))

            if p_width > 0 and p_height > 0:
                txt_overlay = Image.new("RGBA", (p_width, p_height), (255, 255, 255, 0))
                overlay_draw = ImageDraw.Draw(txt_overlay)

                # Convert anchor coordinate to preview space
                px, py = original_to_preview(
                    self.state.text_x, self.state.text_y, scale, (offset_x, offset_y)
                )
                anchor = get_text_anchor(self.state.alignment)

                # Draw text onto overlay
                preview_font = ImageFont.truetype(font_path, int(final_size * scale))
                overlay_draw.text(
                    (px - px_left, py - py_top),
                    preview_name,
                    font=preview_font,
                    fill=self.state.text_color,
                    anchor=anchor,
                )

                self.photo_text_image = ImageTk.PhotoImage(txt_overlay)
                self.text_item = self.create_image(
                    px_left, py_top, anchor="nw", image=self.photo_text_image
                )

                if self.is_dragging:
                    # Draw dotted bounding box
                    self.bbox_id = self.create_rectangle(
                        px_left,
                        py_top,
                        px_right,
                        py_bottom,
                        dash=(4, 4),
                        outline="blue",
                    )

                    canvas_center_x, canvas_center_y = original_to_preview(
                        self.state.template_width / 2,
                        self.state.template_height / 2,
                        scale,
                        (offset_x, offset_y),
                    )

                    self.v_guide = self.create_line(
                        canvas_center_x,
                        0,
                        canvas_center_x,
                        self.winfo_height(),
                        fill="red",
                        dash=(2, 2),
                    )
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
