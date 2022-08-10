import contextlib
import functools
from dataclasses import dataclass

from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.figure import Figure

from pyquibbler.quib import Quib

from matplotlib.testing.decorators import image_comparison


@dataclass
class RedrawCount:
    count: int


@contextlib.contextmanager
def count_canvas_draws(canvas: FigureCanvasBase):
    canvas_class = type(canvas)
    previous_draw = canvas_class.draw
    redraw_count = RedrawCount(0)

    def draw(*args, **kwargs):
        nonlocal redraw_count
        redraw_count.count += 1
        return previous_draw(*args, **kwargs)

    canvas_class.draw = draw

    yield redraw_count

    canvas_class.draw = previous_draw


@contextlib.contextmanager
def count_redraws(widget_quib: Quib):
    previous_redraw = widget_quib.handler.reevaluate_graphic_quib
    redraw_count = RedrawCount(0)

    def redraw(*args, **kwargs):
        nonlocal redraw_count
        redraw_count.count += 1
        return previous_redraw(*args, **kwargs)

    widget_quib.handler.reevaluate_graphic_quib = redraw

    yield redraw_count

    widget_quib.handler.reevaluate_graphic_quib = previous_redraw


quibbler_image_comparison = functools.partial(image_comparison, remove_text=True, extensions=['png'],
                                              savefig_kwarg=dict(dpi=100))
