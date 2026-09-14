from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    draw_mark,
    heat_map,
    make_board,
    make_command_card,
    make_event_card,
    make_code_panel,
    make_x,
    make_o,
    set_voice,
)


class StyleTest(VoiceoverScene):
    def construct(self):
        set_voice(self)
        self.camera.background_color = BG_COLOR
        with self.voiceover(text="This is the style test. <bookmark mark='board'/>Here is a board, a mark, and a code panel.") as tracker:
            title = Text("Style test", font_size=40, color="#E6E6E6").to_edge(UP, buff=0.4)
            self.play(Write(title))
            self.wait_until_bookmark("board")
            board = make_board().move_to([-3.6, -0.3, 0])
            x_mark = make_x().move_to(board[0].get_center())
            o_mark = make_o().move_to(board[4].get_center())
            code = make_code_panel("def f(x):\n    return x * 2\n\n\nprint(f(21))").move_to([3.4, -0.3, 0])
            cmd = make_command_card("PlaceMark", ["game_id: g1", "position: (1, 1)"]).move_to([-3.6, -3.2, 0])
            ev = make_event_card("GameWon", ["winner: O", "line: 2, 4, 6"]).move_to([3.4, -3.2, 0])
            self.play(FadeIn(board), FadeIn(code))
            self.play(Write(x_mark), Write(o_mark), FadeIn(cmd), FadeIn(ev))
            cells = heat_map(board, [None, None, 0.1, None, None, None, 0.5, 0.2, None])
            self.play(FadeIn(cells))
            self.wait(1)
