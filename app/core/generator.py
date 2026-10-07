import re
from pathlib import Path
from queue import Queue
from threading import Event, Thread

from PIL import Image, ImageDraw, ImageFont

from app.core.renderer import auto_fit_font_size, get_text_anchor
from app.core.state import AppState


def sanitize_filename(name: str) -> str:
    """
    Remove illegal Windows filename characters and clean up the result.
    """
    # Replace illegal characters with underscore
    illegal_chars = r'[\\/:*?"<>|]'
    cleaned = re.sub(illegal_chars, "_", name)

    # Remove control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", cleaned)

    # Collapse spaces around underscores
    cleaned = re.sub(r"\s*_\s*", "_", cleaned)

    # Collapse multiple underscores
    cleaned = re.sub(r"_+", "_", cleaned)

    # Strip leading/trailing whitespace, dots, and underscores
    cleaned = cleaned.strip(" ._")

    return cleaned


def get_unique_filename(
    base_name: str, output_folder: Path, generated_names: set
) -> Path:
    """
    Find a unique filename in the output folder.
    """
    safe_name = sanitize_filename(base_name)
    if not safe_name:
        safe_name = "Certificate"

    candidate = f"{safe_name}.png"
    counter = 2

    # Check both filesystem and the set of names generated in this run
    while (output_folder / candidate).exists() or candidate.lower() in generated_names:
        candidate = f"{safe_name}_{counter}.png"
        counter += 1

    generated_names.add(candidate.lower())
    return output_folder / candidate


class GeneratorThread(Thread):
    def __init__(self, state: AppState, progress_queue: Queue, cancel_event: Event):
        super().__init__()
        self.state = state
        self.progress_queue = progress_queue
        self.cancel_event = cancel_event

    def run(self):
        if not self.state.template_path or not self.state.output_folder:
            self.progress_queue.put(
                {"type": "error", "message": "Missing required data for generation."}
            )
            return

        rows = self.state.raw_data
        if not rows and self.state.names:
            col = self.state.filename_column or "Name"
            rows = [{col: n} for n in self.state.names]

        if not rows:
            self.progress_queue.put(
                {"type": "error", "message": "No participant data found for generation."}
            )
            return

        # Determine enabled fields
        enabled_fields = [f for f in self.state.fields if f.enabled]
        if not enabled_fields:
            fallback_field = self.state.active_field
            if fallback_field is not None:
                enabled_fields = [fallback_field]
            else:
                self.progress_queue.put(
                    {
                        "type": "error",
                        "message": "No fields are selected to appear on the certificate.",
                    }
                )
                return

        generated_files = set()
        completed = 0
        failed = 0
        errors = []
        total = len(rows)

        for i, row in enumerate(rows):
            if self.cancel_event.is_set():
                self.progress_queue.put({"type": "cancelled"})
                break

            # Find a representative name for logs and filename
            primary_col = self.state.filename_column
            display_name = ""
            if primary_col and primary_col in row and str(row[primary_col]).strip():
                display_name = str(row[primary_col]).strip()
            else:
                for f in enabled_fields:
                    val = str(row.get(f.column_name, "")).strip()
                    if val:
                        display_name = val
                        break

            if not display_name:
                display_name = f"Certificate_{i+1}"

            try:
                # 1. Re-open template
                with Image.open(self.state.template_path) as img:
                    img.load()
                    draw = ImageDraw.Draw(img)

                    # 2. Draw all enabled fields
                    for field_cfg in enabled_fields:
                        text_val = str(row.get(field_cfg.column_name, "")).strip()
                        if not text_val:
                            continue

                        font_path = (
                            str(field_cfg.font_path) if field_cfg.font_path else ""
                        )

                        # Determine font size (with auto-fit if configured)
                        final_size = field_cfg.font_size
                        if field_cfg.auto_fit and font_path:
                            safe_margin_px = (
                                self.state.template_width * field_cfg.safe_margin_pct
                            )
                            max_width = self.state.template_width - (
                                2 * safe_margin_px
                            )
                            final_size = auto_fit_font_size(
                                draw,
                                text_val,
                                font_path,
                                field_cfg.font_size,
                                max_width,
                            )

                        font = (
                            ImageFont.truetype(font_path, final_size)
                            if font_path
                            else ImageFont.load_default()
                        )
                        anchor = get_text_anchor(field_cfg.alignment)

                        draw.text(
                            (field_cfg.text_x, field_cfg.text_y),
                            text_val,
                            font=font,
                            fill=field_cfg.text_color,
                            anchor=anchor,
                        )

                    # 3. Determine unique filename
                    base_name = sanitize_filename(display_name)
                    if not base_name:
                        base_name = f"Certificate_{i+1}"
                    output_path = get_unique_filename(
                        base_name, self.state.output_folder, generated_files
                    )

                    # 4. Save image
                    if img.mode == "P":
                        if "transparency" in img.info:
                            img = img.convert("RGBA")
                        else:
                            img = img.convert("RGB")

                    img.save(output_path, "PNG")
                    completed += 1

            except Exception as e:  # noqa: BLE001
                failed += 1
                errors.append({"row": i + 1, "name": display_name, "error": str(e)})

            # Report progress
            self.progress_queue.put(
                {
                    "type": "progress",
                    "completed": completed,
                    "failed": failed,
                    "total": total,
                    "current_name": display_name,
                }
            )

        self.progress_queue.put(
            {"type": "done", "completed": completed, "failed": failed, "errors": errors}
        )

