from typing import Tuple
from PIL import ImageDraw, ImageFont

def measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> Tuple[int, int, int, int]:
    """
    Measure text bounding box accurately.
    Returns (left, top, right, bottom).
    """
    return draw.textbbox((0, 0), text, font=font)


def calculate_text_position(
    text_bbox: Tuple[int, int, int, int],
    text_x: float,
    text_y: float,
    alignment: str,
) -> Tuple[float, float]:
    """
    Calculate the (x, y) starting coordinate for ImageDraw.text based on
    the stored text_x/text_y (which acts as the anchor) and the requested alignment.
    
    text_bbox is (left, top, right, bottom).
    text_x, text_y is the anchor position.
    """
    left, top, right, bottom = text_bbox
    width = right - left
    height = bottom - top

    # The anchor Y is considered the vertical center of the text bounding box.
    # We want to find the top-left coordinate to pass to `draw.text()`.
    # Pillow's draw.text with anchor="lt" (default) requires the top-left coordinate.
    
    # Calculate top-left Y
    draw_y = text_y - (height / 2.0) - top
    
    if alignment == "center":
        draw_x = text_x - (width / 2.0) - left
    elif alignment == "left":
        draw_x = text_x - left
    elif alignment == "right":
        draw_x = text_x - width - left
    else:
        # Default to center if unknown
        draw_x = text_x - (width / 2.0) - left
        
    return draw_x, draw_y

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
            bbox = measure_text(draw, text, font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                return size
            size -= 1
        except Exception:
            break
    return size
