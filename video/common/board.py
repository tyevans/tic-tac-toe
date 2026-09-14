from manim import *

from common.style import (
    BOARD_SIDE,
    BOARD_STROKE_COLOR,
    BOARD_STROKE_WIDTH,
    MARK_FRACTION,
    MUTED_COLOR,
    O_COLOR,
    POSITIVE_COLOR,
    TEXT_COLOR,
    X_COLOR,
)


def make_board(side: float = BOARD_SIDE) -> VGroup:
    squares = VGroup(
        *[
            Square(
                side_length=side,
                stroke_color=BOARD_STROKE_COLOR,
                stroke_width=BOARD_STROKE_WIDTH,
                fill_opacity=0,
            )
            for _ in range(9)
        ]
    ).arrange_in_grid(rows=3, cols=3, buff=0)
    return squares


def make_x(color: str = X_COLOR, scale: float = 1.0) -> VGroup:
    half = BOARD_SIDE * MARK_FRACTION / 2
    line1 = Line([-half, -half, 0], [half, half, 0], stroke_color=color, stroke_width=6)
    line2 = Line([-half, half, 0], [half, -half, 0], stroke_color=color, stroke_width=6)
    return VGroup(line1, line2).scale(scale)


def make_o(color: str = O_COLOR, scale: float = 1.0) -> Circle:
    return Circle(
        radius=BOARD_SIDE * MARK_FRACTION / 2,
        color=color,
        stroke_width=6,
    ).scale(scale)


def draw_mark(board: VGroup, index: int, player: str) -> VGroup:
    color = X_COLOR if player == "X" else O_COLOR
    mark = make_x(color) if player == "X" else make_o(color)
    mark.move_to(board[index].get_center())
    return mark


def cell_indices(board: VGroup, font_size: int = 22, color: str = MUTED_COLOR) -> VGroup:
    return VGroup(
        *[
            Text(str(i), font_size=font_size, color=color).move_to(
                board[i].get_corner(UL) + RIGHT * 0.18 + DOWN * 0.18
            )
            for i in range(9)
        ]
    )


def heat_map(board: VGroup, probs: list[float | None]) -> VGroup:
    cells = VGroup()
    for i, p in enumerate(probs):
        if p is None:
            continue
        rect = Square(side_length=BOARD_SIDE * 0.98, stroke_opacity=0)
        rect.set_fill(POSITIVE_COLOR, opacity=p)
        rect.move_to(board[i].get_center())
        label = Text(f"{p:.2f}", font_size=22, color=TEXT_COLOR)
        label.move_to(board[i].get_center())
        cells.add(VGroup(rect, label))
    return cells
