import contextlib
import functools
from dataclasses import dataclass
from pyquibbler.quib import Quib

from matplotlib.testing.decorators import image_comparison


@dataclass
class RedrawCount:
    count: int


@contextlib.contextmanager
def count_redraws(widget_quib: Quib):
    previous_redraw = widget_quib.handler.redraw_if_appropriate
    redraw_count = RedrawCount(0)

    def redraw(*args, **kwargs):
        nonlocal redraw_count
        redraw_count.count += 1
        return previous_redraw(*args, **kwargs)

    widget_quib.handler.redraw_if_appropriate = redraw

    yield redraw_count

    widget_quib.handler.redraw_if_appropriate = previous_redraw


quibbler_image_comparison = functools.partial(image_comparison, remove_text=True, extensions=['png'],
                                              savefig_kwarg=dict(dpi=100))
