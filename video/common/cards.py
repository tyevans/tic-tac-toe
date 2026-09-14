from manim import *

from common.board import make_board, make_x
from common.style import COMMAND_COLOR, EVENT_COLOR, MUTED_COLOR, TEXT_COLOR


def _make_card(title: str, fields: list[str], color: str) -> VGroup:
    title_text = Text(title, font_size=24, weight=BOLD, color=color)
    field_texts = VGroup(
        *[Text(f, font_size=18, color=MUTED_COLOR) for f in fields]
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    content = VGroup(title_text, field_texts).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    box = RoundedRectangle(
        corner_radius=0.12,
        width=content.width + 0.3,
        height=content.height + 0.24,
        stroke_color=color,
        stroke_width=3,
        fill_opacity=0,
    )
    content.move_to(box)
    return VGroup(box, content)


def make_command_card(title: str, fields: list[str]) -> VGroup:
    return _make_card(title, fields, COMMAND_COLOR)


def make_event_card(title: str, fields: list[str]) -> VGroup:
    return _make_card(title, fields, EVENT_COLOR)


def make_game_card(game_id: str = "g1") -> VGroup:
    box = RoundedRectangle(
        width=5.4,
        height=3.6,
        corner_radius=0.12,
        stroke_color=TEXT_COLOR,
        stroke_width=3,
        fill_opacity=0,
    )
    header = Text("Game", font_size=32, weight=BOLD, color=TEXT_COLOR)
    row1 = Text(f"id: {game_id}", font_size=18, color=MUTED_COLOR)
    row2 = VGroup(Text("board:", font_size=18, color=MUTED_COLOR), make_board().scale(0.35)).arrange(RIGHT, buff=0.15)
    row3 = VGroup(Text("current_player:", font_size=18, color=MUTED_COLOR), make_x().scale(0.3)).arrange(RIGHT, buff=0.15)
    row4 = Text("status: IN_PROGRESS", font_size=18, color=MUTED_COLOR)
    rows = VGroup(row1, row2, row3, row4).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    content = VGroup(header, rows).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    content.move_to(box)
    return VGroup(box, header, row1, row2, row3, row4)
