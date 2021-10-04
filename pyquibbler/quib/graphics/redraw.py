import contextlib
from matplotlib.axes import Axes

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


def redraw_axes(axes: Axes, force: bool = False):
    """
    Actual redrawing of axes- this should be WITHOUT rendering anything except for the new artists
    """
    if IN_AGGREGATE_REDRAW_MODE and not force:
        AXESES_TO_REDRAW.add(axes)
        return

    with timer(name="redraw"):
        # if the renderer cache is None, we've never done an initial draw- which means we can just wait for the
        # initial draw to happen which will naturally use our updated artists
        if axes.get_renderer_cache() is not None:
            if axes.figure.canvas.supports_blit:
                # redraw_in_frame is supposed to be a quick way to redraw all artists in an axes- the expectation is
                # that the renderer will not rerender any artists that already exist.
                # We saw that the performance matched the performance of what automatically happens when pausing
                # (which causes a the event loop to run)
                axes.redraw_in_frame()
                # # After redrawing to the canvas, we now need to blit the bitmap to the GUI
                axes.figure.canvas.blit(axes.bbox)
            else:
                axes.figure.canvas.draw()
