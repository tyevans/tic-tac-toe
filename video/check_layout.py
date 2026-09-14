import importlib.util
import sys
from pathlib import Path

from manim import Text, config


def load_scene(path: Path, class_name: str):
    spec = importlib.util.spec_from_file_location("scene_mod_" + class_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, class_name)


def frame_bounds():
    return config.frame_width / 2, config.frame_height / 2


def all_submobjects(mo):
    yield mo
    for sub in mo.submobjects:
        yield from all_submobjects(sub)


def boxes_overlap(a, b, tol: float = 0.05) -> bool:
    a_left, a_down = a[0], a[1]
    a_right, a_up = a[2], a[3]
    b_left, b_down = b[0], b[1]
    b_right, b_up = b[2], b[3]
    x_overlap = min(a_right, b_right) - max(a_left, b_left)
    y_overlap = min(a_up, b_up) - max(a_down, b_down)
    return x_overlap > tol and y_overlap > tol


def bbox(mo):
    min_x, min_y = mo.get_left()[0], mo.get_bottom()[1]
    max_x, max_y = mo.get_right()[0], mo.get_top()[1]
    return min_x, min_y, max_x, max_y


def text_name(mo) -> str:
    if isinstance(mo, Text):
        return f"Text({mo.text[:40]!r})"
    return mo.__class__.__name__


def check_scene(path: Path, class_name: str, margin: float = 0.02) -> int:
    config.update({"save_last_frame": True})
    scene_class = load_scene(path, class_name)
    scene = scene_class()
    scene.render()
    half_w, half_h = frame_bounds()
    problems: list[str] = []
    final = list(scene.mobjects)

    texts = []
    for mo in final:
        for sub in all_submobjects(mo):
            bb = bbox(sub)
            if (
                bb[0] < -half_w - margin
                or bb[2] > half_w + margin
                or bb[1] < -half_h - margin
                or bb[3] > half_h + margin
            ):
                problems.append(f"OUT OF FRAME: {text_name(sub)} bbox={tuple(round(v, 2) for v in bb)}")
        for sub in all_submobjects(mo):
            if isinstance(sub, Text):
                texts.append(sub)
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if boxes_overlap(bbox(texts[i]), bbox(texts[j])):
                problems.append(
                    f"TEXT OVERLAP: {texts[i].text[:40]!r} and {texts[j].text[:40]!r}"
                )
    if problems:
        print(f"FAIL {class_name}:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"OK {class_name}: {len(final)} top-level mobjects, {len(texts)} texts in final state")
    return 0


if __name__ == "__main__":
    target = sys.argv[1]
    class_name = sys.argv[2]
    scene_dir = Path(target).parent
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(scene_dir))
    sys.exit(check_scene(Path(target), class_name))
