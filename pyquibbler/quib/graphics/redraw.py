from __future__ import annotations
import contextlib
from typing import Set, TYPE_CHECKING
from matplotlib.axes import Axes

from pyquibbler.logger import logger
from pyquibbler.performance_utils import timer
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus

if TYPE_CHECKING:
    from pyquibbler.quib import GraphicsFunctionQuib


QUIBS_TO_REDRAW: Set[GraphicsFunctionQuib] = set()
IN_AGGREGATE_REDRAW_MODE = False


@contextlib.contextmanager
def aggregate_redraw_mode():
    """
    In aggregate redraw mode, no axeses will be redrawn until the end of the context manager (unless force=True
    was used when redrawing)
    """
    global IN_AGGREGATE_REDRAW_MODE
    if IN_AGGREGATE_REDRAW_MODE:
        yield
    else:
        IN_AGGREGATE_REDRAW_MODE = True
        yield
        IN_AGGREGATE_REDRAW_MODE = False
        _redraw_graphics_function_quibs()


def _redraw_graphics_function_quibs():
    quibs_that_are_invalid = [quib for quib in QUIBS_TO_REDRAW if quib.cache_status != CacheStatus.ALL_VALID]
    with timer("quib redraw", lambda x: logger.info(f"redrawing {len(quibs_that_are_invalid)} quibs: {x}s")):
        for graphics_function_quib in quibs_that_are_invalid:
            graphics_function_quib.redraw_if_appropriate()
    axeses = {axes for graphics_function_quib in quibs_that_are_invalid
              for axes in graphics_function_quib.get_axeses()}
    redraw_axeses(axeses)
    QUIBS_TO_REDRAW.clear()


def redraw_graphics_function_quibs_or_add_in_aggregate_mode(graphics_function_quibs: Set[GraphicsFunctionQuib]):
    global QUIBS_TO_REDRAW
    if IN_AGGREGATE_REDRAW_MODE:
        QUIBS_TO_REDRAW |= graphics_function_quibs
    else:
        QUIBS_TO_REDRAW = graphics_function_quibs
        _redraw_graphics_function_quibs()


def redraw_axeses(axeses: Set[Axes]):
    """
    Actual redrawing of axes- this should be WITHOUT rendering anything except for the new artists
    """
    canvases = {axes.figure.canvas for axes in axeses}
    with timer("redraw", lambda x: logger.info(f"redraw {len(axeses)} axeses, {len(canvases)} canvases {x}s")):
        for canvas in canvases:
            canvas.draw()
