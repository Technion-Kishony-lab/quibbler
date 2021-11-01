import contextlib
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
    for axes in AXESES_TO_REDRAW:
        redraw_axes(axes)
    AXESES_TO_REDRAW.clear()


def redraw_axes(axes: Axes, force: bool = False):
    """
    Actual redrawing of axes- this should be WITHOUT rendering anything except for the new artists
    """
    if IN_AGGREGATE_REDRAW_MODE and not force:
        AXESES_TO_REDRAW.add(axes)
    else:
        with timer(name="redraw", callback=lambda t: logger.info(f"redraw canvas {t}")):
            axes.figure.canvas.draw()
