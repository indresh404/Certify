def preview_to_original(
    px: float, py: float, scale: float, offset: tuple[float, float]
) -> tuple[float, float]:
    """Convert a point in preview/canvas space to original-image space."""
    if scale == 0:
        return 0.0, 0.0
    ox = (px - offset[0]) / scale
    oy = (py - offset[1]) / scale
    return ox, oy


def original_to_preview(
    ox: float, oy: float, scale: float, offset: tuple[float, float]
) -> tuple[float, float]:
    """Convert a point in original-image space to preview/canvas space."""
    px = ox * scale + offset[0]
    py = oy * scale + offset[1]
    return px, py
