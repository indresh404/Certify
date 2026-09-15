from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppState:
    template_path: Path | None = None
    template_width: int = 0
    template_height: int = 0

    csv_path: Path | None = None
    headers: list[str] = field(default_factory=list)
    raw_data: list[dict] = field(default_factory=list)
    name_column: str = "Name"
    names: list[str] = field(default_factory=list)

    font_name: str = "OpenSans-Regular"
    font_path: Path | None = None  # set if user browsed a custom font
    font_size: int = 48
    bold: bool = False
    italic: bool = False
    text_color: str = "#000000"
    alignment: str = "center"  # left | center | right
    auto_fit: bool = False
    safe_margin_pct: float = 0.05

    text_x: float = 0.0  # ORIGINAL image coordinates, always
    text_y: float = 0.0

    preview_scale: float = 1.0
    preview_offset: tuple[float, float] = (0.0, 0.0)

    output_folder: Path | None = None
