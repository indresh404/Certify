from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FieldConfig:
    column_name: str
    enabled: bool = True
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


@dataclass
class AppState:
    template_path: Path | None = None
    template_width: int = 0
    template_height: int = 0

    csv_path: Path | None = None
    headers: list[str] = field(default_factory=list)
    raw_data: list[dict] = field(default_factory=list)
    filename_column: str = "Name"

    fields: list[FieldConfig] = field(default_factory=list)
    active_field_index: int = 0

    preview_scale: float = 1.0
    preview_offset: tuple[float, float] = (0.0, 0.0)

    output_folder: Path | None = None

    def _ensure_active_field(self) -> FieldConfig:
        if not self.fields:
            default_field = FieldConfig(
                column_name=self.filename_column or "Name",
                text_x=self.template_width / 2 if self.template_width else 0.0,
                text_y=self.template_height / 2 if self.template_height else 0.0,
            )
            self.fields.append(default_field)
            self.active_field_index = 0
        if self.active_field_index < 0:
            self.active_field_index = 0
        elif self.active_field_index >= len(self.fields):
            self.active_field_index = max(0, len(self.fields) - 1)
        return self.fields[self.active_field_index]

    @property
    def active_field(self) -> FieldConfig | None:
        if 0 <= self.active_field_index < len(self.fields):
            return self.fields[self.active_field_index]
        return None

    def get_field(self, column_name: str) -> FieldConfig | None:
        for f in self.fields:
            if f.column_name == column_name:
                return f
        return None

    def add_field(
        self,
        column_name: str,
        font_name: str = "OpenSans-Regular",
        font_path: Path | None = None,
    ) -> FieldConfig:
        w = self.template_width or 800
        h = self.template_height or 600
        count = len(self.fields)
        text_y = (h * 0.4) + (count * 60) if count > 0 else (h / 2.0)
        new_field = FieldConfig(
            column_name=column_name,
            enabled=True,
            font_name=font_name,
            font_path=font_path,
            text_x=w / 2.0,
            text_y=text_y,
        )
        self.fields.append(new_field)
        self.active_field_index = len(self.fields) - 1
        return new_field

    def remove_field(self, index: int):
        if 0 <= index < len(self.fields):
            self.fields.pop(index)
            if self.active_field_index >= len(self.fields):
                self.active_field_index = max(0, len(self.fields) - 1)


    # Backward compatibility properties
    @property
    def name_column(self) -> str:
        return self.filename_column

    @name_column.setter
    def name_column(self, val: str):
        self.filename_column = val

    @property
    def names(self) -> list[str]:
        col = self.filename_column or (self.headers[0] if self.headers else "Name")
        return [
            str(row.get(col, "")).strip().title()
            for row in self.raw_data
            if str(row.get(col, "")).strip()
        ]

    @names.setter
    def names(self, val: list[str]):
        col = self.filename_column or "Name"
        self.raw_data = [{col: name} for name in val]
        if not self.headers:
            self.headers = [col]
        if not self.fields:
            self.fields = [
                FieldConfig(
                    column_name=col,
                    text_x=self.template_width / 2 if self.template_width else 0.0,
                    text_y=self.template_height / 2 if self.template_height else 0.0,
                )
            ]

    @property
    def text_x(self) -> float:
        return self._ensure_active_field().text_x

    @text_x.setter
    def text_x(self, val: float):
        self._ensure_active_field().text_x = val

    @property
    def text_y(self) -> float:
        return self._ensure_active_field().text_y

    @text_y.setter
    def text_y(self, val: float):
        self._ensure_active_field().text_y = val

    @property
    def font_size(self) -> int:
        return self._ensure_active_field().font_size

    @font_size.setter
    def font_size(self, val: int):
        self._ensure_active_field().font_size = val

    @property
    def font_name(self) -> str:
        return self._ensure_active_field().font_name

    @font_name.setter
    def font_name(self, val: str):
        self._ensure_active_field().font_name = val

    @property
    def font_path(self) -> Path | None:
        return self._ensure_active_field().font_path

    @font_path.setter
    def font_path(self, val: Path | None):
        self._ensure_active_field().font_path = val

    @property
    def text_color(self) -> str:
        return self._ensure_active_field().text_color

    @text_color.setter
    def text_color(self, val: str):
        self._ensure_active_field().text_color = val

    @property
    def alignment(self) -> str:
        return self._ensure_active_field().alignment

    @alignment.setter
    def alignment(self, val: str):
        self._ensure_active_field().alignment = val

    @property
    def auto_fit(self) -> bool:
        return self._ensure_active_field().auto_fit

    @auto_fit.setter
    def auto_fit(self, val: bool):
        self._ensure_active_field().auto_fit = val

    @property
    def safe_margin_pct(self) -> float:
        return self._ensure_active_field().safe_margin_pct

    @safe_margin_pct.setter
    def safe_margin_pct(self, val: float):
        self._ensure_active_field().safe_margin_pct = val
