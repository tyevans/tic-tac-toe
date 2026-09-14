from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    EVENT_COLOR,
    MUTED_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    set_voice,
)

TERMS = (
    ("Domain", "the subject: tic-tac-toe", TEXT_COLOR),
    ("Value object", "data that checks itself", TEXT_COLOR),
    ("Invariant", "a rule that is always true", RULE_COLOR),
    ("DomainError", "raised when a rule breaks", ERROR_COLOR),
    ("Aggregate", "Game: owns the rules", TEXT_COLOR),
    ("Transition", "next Game + what happened", EVENT_COLOR),
)


class E1S3DomainWords(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def _make_cards(self) -> VGroup:
        contents = []
        for term, definition, color in TERMS:
            term_text = Text(term, font_size=24, weight=BOLD, color=color)
            def_text = Text(definition, font_size=18, color=MUTED_COLOR)
            content = VGroup(term_text, def_text).arrange(RIGHT, buff=0.35, aligned_edge=ORIGIN)
            contents.append((content, color))
        max_w = max(c.width for c, _ in contents)
        max_h = max(c.height for c, _ in contents)
        cards = VGroup()
        for content, color in contents:
            box = RoundedRectangle(
                corner_radius=0.12,
                width=max_w + 0.7,
                height=max_h + 0.32,
                stroke_color=color,
                stroke_width=3,
                fill_opacity=0,
            )
            content.align_to(box, LEFT).shift(RIGHT * 0.35)
            cards.add(VGroup(box, *content))
        return cards

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("Words for the domain", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        cards = self._make_cards()
        cards.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        cards.next_to(title, DOWN, buff=0.3)
        with self.voiceover(
            "Before we read the code, we need six words. <bookmark mark='domain'/>"
            "The domain is the subject of the program. Here, the domain is tic-tac-toe."
        ) as tracker:
            self.play(Write(title))
            self.wait_until_bookmark("domain")
            self.play(FadeIn(cards[0], shift=RIGHT * 0.3))
        with self.voiceover(
            "<bookmark mark='value_object'/>A value object is a small piece of data. "
            "It checks itself when Python makes it. "
            "<bookmark mark='invariant'/>An invariant is a rule that must always be true. "
            "For example: a board has nine cells."
        ) as tracker:
            self.wait_until_bookmark("value_object")
            self.play(FadeIn(cards[1], shift=RIGHT * 0.3))
            self.wait_until_bookmark("invariant")
            self.play(FadeIn(cards[2], shift=RIGHT * 0.3))
        with self.voiceover(
            "<bookmark mark='domain_error'/>If a value breaks an invariant, the code raises a Domain Error. "
            "<bookmark mark='aggregate'/>An aggregate is the one object that owns the rules for a group of data. "
            "Here, the aggregate is Game. "
            "<bookmark mark='transition'/>A Transition is the result of a move: the next Game, and a list of what happened."
        ) as tracker:
            self.wait_until_bookmark("domain_error")
            self.play(FadeIn(cards[3], shift=RIGHT * 0.3))
            self.wait_until_bookmark("aggregate")
            self.play(FadeIn(cards[4], shift=RIGHT * 0.3))
            self.wait_until_bookmark("transition")
            self.play(FadeIn(cards[5], shift=RIGHT * 0.3))
        self.play(Indicate(cards))
        self.wait(1)
