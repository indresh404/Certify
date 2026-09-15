import re

with open("app/core/generator.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix import
content = re.sub(
    r"from app\.core\.renderer import auto_fit_font_size, calculate_text_position, measure_text",
    "from app.core.renderer import auto_fit_font_size, get_text_anchor",
    content,
)

# Fix draw logic
old_logic = """                    bbox = measure_text(draw, name, font)
                    draw_x, draw_y = calculate_text_position(
                        bbox,
                        self.app_state.text_x,
                        self.app_state.text_y,
                        self.app_state.alignment,
                    )

                    # 4. Draw text
                    draw.text(
                        (draw_x, draw_y),
                        name,
                        font=font,
                        fill=self.app_state.text_color,
                    )"""

new_logic = """                    anchor = get_text_anchor(self.app_state.alignment)

                    # 4. Draw text
                    draw.text(
                        (self.app_state.text_x, self.app_state.text_y),
                        name,
                        font=font,
                        fill=self.app_state.text_color,
                        anchor=anchor
                    )"""

content = content.replace(old_logic, new_logic)

with open("app/core/generator.py", "w", encoding="utf-8") as f:
    f.write(content)
