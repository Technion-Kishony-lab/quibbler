import contextlib
from typing import Set

from matplotlib.axes import Axes

from pyquibbler.logger import logger
from pyquibbler.performance_utils import timer

AXESES_TO_REDRAW = set()
IN_AGGREGATE_REDRAW_MODE = False


@contextlib.contextmanager
def aggregate_redraw_mode():
    """
    In aggregate redraw mode, no axeses will be redrawn until the end of the context manager (unless force=True
    was used when redrawing)
    """
    global IN_AGGREGATE_REDRAW_MODE
    IN_AGGREGATE_REDRAW_MODE = True
    yield
    IN_AGGREGATE_REDRAW_MODE = False
    redraw_axeses(AXESES_TO_REDRAW)
    AXESES_TO_REDRAW.clear()


def redraw_axeses(axeses: Set[Axes], force: bool = False):
    """
    Actual redrawing of axes- this should be WITHOUT rendering anything except for the new artists
    """
    if IN_AGGREGATE_REDRAW_MODE and not force:
        AXESES_TO_REDRAW.update(axeses)
    else:
        canvases = {axes.figure.canvas for axes in axeses}
        with timer(name="redraw", callback=lambda t: logger.info(f"redraw canvas {t}")):
            for canvas in canvases:
                canvas.draw()
