import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk

from app.core.coordinates import original_to_preview
from app.core.renderer import auto_fit_font_size, get_text_anchor, measure_text_anchored
from app.core.state import AppState


class PreviewCanvas(ctk.CTkCanvas):
    def __init__(
        self,
        master,
        state: AppState,
        on_change_callback,
        on_field_selected_callback=None,
        on_drag_callback=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.state = state
        self.on_change = on_change_callback
        self.on_field_selected = on_field_selected_callback
        self.on_drag_callback = on_drag_callback

        self.bind("<Configure>", self.on_resize)

        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)

        # Debounce resize
        self.resize_after_id = None

        self.photo_image = None
        self.bg_image_id = None

        self.text_overlay_items = []
        self.photo_text_images = []
        self.bbox_items = []
        self.guide_items = []
        self.field_bounds = []

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
        self.text_overlay_items.clear()
        self.photo_text_images.clear()
        self.bbox_items.clear()
        self.guide_items.clear()

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
        # Delete old overlay elements
        for item_id in self.text_overlay_items:
            self.delete(item_id)
        self.text_overlay_items.clear()
        self.photo_text_images.clear()

        for item_id in self.bbox_items:
            self.delete(item_id)
        self.bbox_items.clear()

        for item_id in self.guide_items:
            self.delete(item_id)
        self.guide_items.clear()

        self.field_bounds.clear()

        if not self.state.template_path or not self.state.fields:
            return

        scale = self.state.preview_scale
        offset_x, offset_y = self.state.preview_offset

        # Draw each enabled field
        for idx, field_cfg in enumerate(self.state.fields):
            if not field_cfg.enabled:
                continue

            # Determine sample text to preview
            sample_text = ""
            if self.state.raw_data:
                sample_text = str(
                    self.state.raw_data[0].get(field_cfg.column_name, "")
                ).strip()
            if not sample_text:
                sample_text = f"Sample {field_cfg.column_name}"

            # Auto-fit calculation
            final_size = field_cfg.font_size
            font_path = str(field_cfg.font_path) if field_cfg.font_path else ""

            if field_cfg.auto_fit and font_path:
                try:
                    safe_margin_px = (
                        self.state.template_width * field_cfg.safe_margin_pct
                    )
                    max_width = self.state.template_width - (2 * safe_margin_px)
                    dummy_img = Image.new("RGB", (1, 1))
                    draw = ImageDraw.Draw(dummy_img)
                    final_size = auto_fit_font_size(
                        draw, sample_text, font_path, field_cfg.font_size, max_width
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

                # Measure bounding box in original template coordinates
                bbox = measure_text_anchored(
                    draw,
                    sample_text,
                    font,
                    field_cfg.text_x,
                    field_cfg.text_y,
                    field_cfg.alignment,
                )

                left, top, right, bottom = bbox
                px_left, py_top = original_to_preview(
                    left, top, scale, (offset_x, offset_y)
                )
                px_right, py_bottom = original_to_preview(
                    right, bottom, scale, (offset_x, offset_y)
                )

                self.field_bounds.append(
                    {
                        "index": idx,
                        "field": field_cfg,
                        "bounds": (px_left, py_top, px_right, py_bottom),
                    }
                )

                p_width = max(1, int(px_right - px_left) + 4)
                p_height = max(1, int(py_bottom - py_top) + 4)

                if p_width > 0 and p_height > 0:
                    txt_overlay = Image.new(
                        "RGBA", (p_width, p_height), (255, 255, 255, 0)
                    )
                    overlay_draw = ImageDraw.Draw(txt_overlay)

                    px, py = original_to_preview(
                        field_cfg.text_x,
                        field_cfg.text_y,
                        scale,
                        (offset_x, offset_y),
                    )
                    anchor = get_text_anchor(field_cfg.alignment)
                    scaled_size = max(1, int(final_size * scale))
                    preview_font = (
                        ImageFont.truetype(font_path, scaled_size)
                        if font_path
                        else ImageFont.load_default()
                    )

                    overlay_draw.text(
                        (px - px_left, py - py_top),
                        sample_text,
                        font=preview_font,
                        fill=field_cfg.text_color,
                        anchor=anchor,
                    )

                    photo_img = ImageTk.PhotoImage(txt_overlay)
                    self.photo_text_images.append(photo_img)
                    item_id = self.create_image(
                        px_left, py_top, anchor="nw", image=photo_img
                    )
                    self.text_overlay_items.append(item_id)

                    # If this is the active field, draw selection boundary and badge
                    if idx == self.state.active_field_index:
                        b_id = self.create_rectangle(
                            px_left - 3,
                            py_top - 3,
                            px_right + 3,
                            py_bottom + 3,
                            dash=(4, 4),
                            outline="#3B82F6",
                            width=2,
                        )
                        self.bbox_items.append(b_id)

                        tag_id = self.create_text(
                            px_left - 3,
                            py_top - 6,
                            text=f"• {field_cfg.column_name}",
                            fill="#3B82F6",
                            font=("Arial", 10, "bold"),
                            anchor="sw",
                        )
                        self.bbox_items.append(tag_id)

                        if self.is_dragging:
                            # Center alignment guides
                            canvas_center_x, canvas_center_y = original_to_preview(
                                self.state.template_width / 2,
                                self.state.template_height / 2,
                                scale,
                                (offset_x, offset_y),
                            )

                            v_guide = self.create_line(
                                canvas_center_x,
                                0,
                                canvas_center_x,
                                self.winfo_height(),
                                fill="#EF4444",
                                dash=(2, 2),
                            )
                            h_guide = self.create_line(
                                0,
                                canvas_center_y,
                                self.winfo_width(),
                                canvas_center_y,
                                fill="#EF4444",
                                dash=(2, 2),
                            )
                            self.guide_items.extend([v_guide, h_guide])

            except Exception as e:  # noqa: BLE001
                print(f"Error drawing text preview for {field_cfg.column_name}: {e}")

    def on_press(self, event):
        if not self.state.template_path or not self.state.fields:
            return

        scale = self.state.preview_scale
        if scale <= 0:
            return

        # Hit-test bounding boxes (check from topmost to bottommost)
        hit_index = None
        for item in reversed(self.field_bounds):
            px_left, py_top, px_right, py_bottom = item["bounds"]
            if (px_left - 8 <= event.x <= px_right + 8) and (
                py_top - 8 <= event.y <= py_bottom + 8
            ):
                hit_index = item["index"]
                break

        if hit_index is not None:
            self.state.active_field_index = hit_index
            if self.on_field_selected:
                self.on_field_selected(hit_index)

        active = self.state.active_field
        if active is not None:
            self.is_dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.start_text_x = active.text_x
            self.start_text_y = active.text_y
            self.draw_text_overlay()

    def on_drag(self, event):
        if not self.is_dragging:
            return

        active = self.state.active_field
        if active is None:
            return

        scale = self.state.preview_scale
        if scale <= 0:
            return

        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        ox_delta = dx / scale
        oy_delta = dy / scale

        new_x = self.start_text_x + ox_delta
        new_y = self.start_text_y + oy_delta

        # Snapping thresholds
        snap_threshold_orig = 12.0 / scale

        # Snap to template center X / Y
        template_cx = self.state.template_width / 2
        template_cy = self.state.template_height / 2

        if abs(new_x - template_cx) < snap_threshold_orig:
            new_x = template_cx
        if abs(new_y - template_cy) < snap_threshold_orig:
            new_y = template_cy

        # Snap to other enabled fields' X and Y
        for f in self.state.fields:
            if f.enabled and f is not active:
                if abs(new_x - f.text_x) < snap_threshold_orig:
                    new_x = f.text_x
                if abs(new_y - f.text_y) < snap_threshold_orig:
                    new_y = f.text_y

        active.text_x = new_x
        active.text_y = new_y

        self.draw_text_overlay()

        if self.on_drag_callback:
            self.on_drag_callback()

    def on_release(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.draw_text_overlay()
            if self.on_change:
                self.on_change()

