import contextlib
from dataclasses import dataclass


@dataclass
class RedrawCount:
    count: int


@contextlib.contextmanager
def count_redraws(widget_quib):
    previous_redraw = widget_quib.redraw_if_appropriate
    redraw_count = RedrawCount(0)

    def redraw(*args, **kwargs):
        nonlocal redraw_count
        redraw_count.count += 1
        return previous_redraw(*args, **kwargs)

    widget_quib.redraw_if_appropriate = redraw

    yield redraw_count

    widget_quib.redraw_if_appropriate = previous_redraw
