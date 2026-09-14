from manim import *

from common.style import RULE_COLOR


def make_code_panel(code: str, max_width: float = 6.6, max_height: float = 6.2) -> Code:
    panel = Code(
        code_string=code,
        language="python",
        background="window",
        add_line_numbers=False,
    )
    scale = min(max_width / panel.width, max_height / panel.height, 1.0)
    panel.scale(scale)
    return panel


def code_lines(panel: Code, *numbers: int) -> VGroup:
    paragraph = next(m for m in panel.submobjects if type(m).__name__ == "Paragraph")
    return VGroup(*[paragraph[n] for n in numbers])


def code_highlight(panel: Code, *numbers: int, color: str = RULE_COLOR, buff: float = 0.05) -> SurroundingRectangle:
    selected = code_lines(panel, *numbers)
    lines = VGroup(*[line for line in selected if line.width >= 1e-6 and line.height >= 1e-6])
    return SurroundingRectangle(lines, buff=buff if len(lines) > 0 else 0.0, stroke_color=color, stroke_width=3, corner_radius=0.05)
