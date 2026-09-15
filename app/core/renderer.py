from PIL import ImageDraw, ImageFont


def get_text_anchor(alignment: str) -> str:
    if alignment == "center":
        return "mm"
    elif alignment == "left":
        return "lm"
    elif alignment == "right":
        return "rm"
    return "mm"


def measure_text_anchored(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: float,
    y: float,
    alignment: str,
) -> tuple[int, int, int, int]:
    """
    Measure text bounding box accurately using Pillow's anchor system.
    Returns (left, top, right, bottom).
    """
    anchor = get_text_anchor(alignment)
    return draw.textbbox((x, y), text, font=font, anchor=anchor)


def auto_fit_font_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str,
    initial_size: int,
    max_width: float,
    min_size: int = 8,
) -> int:
    """
    Iteratively reduce font size until the text fits within max_width.
    """
    size = initial_size
    while size > min_size:
        try:
            font = ImageFont.truetype(font_path, size)
            bbox = draw.textbbox((0, 0), text, font=font, anchor="la")
            width = bbox[2] - bbox[0]
            if width <= max_width:
                return size
            size -= 1
        except Exception:  # noqa: BLE001
            break
    return size
