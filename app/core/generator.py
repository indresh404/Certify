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
        if (
            not self.state.template_path
            or not self.state.output_folder
            or not self.state.names
        ):
            self.progress_queue.put(
                {"type": "error", "message": "Missing required data for generation."}
            )
            return

        generated_files = set()
        completed = 0
        failed = 0
        errors = []
        total = len(self.state.names)

        # Calculate safe max width for auto-fit
        safe_margin_px = self.state.template_width * self.state.safe_margin_pct
        max_width = self.state.template_width - (2 * safe_margin_px)

        font_path = str(self.state.font_path) if self.state.font_path else ""

        for i, name in enumerate(self.state.names):
            if self.cancel_event.is_set():
                self.progress_queue.put({"type": "cancelled"})
                break

            try:
                # 1. Re-open template
                with Image.open(self.state.template_path) as img:
                    img.load()

                    draw = ImageDraw.Draw(img)

                    # 2. Determine font size
                    final_size = self.state.font_size
                    if self.state.auto_fit and font_path:
                        final_size = auto_fit_font_size(
                            draw, name, font_path, self.state.font_size, max_width
                        )

                    # 3. Measure text and calculate position
                    font = (
                        ImageFont.truetype(font_path, final_size)
                        if font_path
                        else ImageFont.load_default()
                    )
                    anchor = get_text_anchor(self.state.alignment)

                    # 4. Draw text
                    draw.text(
                        (self.state.text_x, self.state.text_y),
                        name,
                        font=font,
                        fill=self.state.text_color,
                        anchor=anchor,
                    )

                    # 5. Determine unique filename
                    # Note: We fallback to row number if sanitize leaves it empty
                    base_name = (
                        name if sanitize_filename(name) else f"Certificate_{i+1}"
                    )
                    output_path = get_unique_filename(
                        base_name, self.state.output_folder, generated_files
                    )

                    # 6. Save image
                    # Convert to RGB if saving as PNG and image has palette but no transparency (prevent issues)
                    if img.mode == "P":
                        if "transparency" in img.info:
                            img = img.convert("RGBA")
                        else:
                            img = img.convert("RGB")

                    img.save(output_path, "PNG")
                    completed += 1

            except Exception as e:  # noqa: BLE001
                failed += 1
                errors.append({"row": i + 1, "name": name, "error": str(e)})

            # Report progress
            self.progress_queue.put(
                {
                    "type": "progress",
                    "completed": completed,
                    "failed": failed,
                    "total": total,
                    "current_name": name,
                }
            )

        self.progress_queue.put(
            {"type": "done", "completed": completed, "failed": failed, "errors": errors}
        )
