from manim import DOWN, FadeIn, FadeOut, Wiggle

from common.style import ERROR_COLOR


def reject(scene, mob, label):
    scene.play(mob.animate.set_color(ERROR_COLOR), run_time=0.3)
    scene.play(Wiggle(mob), run_time=0.8)
    scene.play(FadeIn(label), run_time=0.4)
    scene.play(FadeOut(mob, shift=DOWN * 0.5), run_time=0.5)
