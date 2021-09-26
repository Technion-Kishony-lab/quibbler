from itertools import chain

from matplotlib.artist import Artist
from matplotlib.axes import Axes

from pyquibbler.quib.utils import call_func_with_quib_values


def redraw_axes(axes: Axes):
    """
    Actual redrawing of axes- this should be WITHOUT rendering anything except for the new artists
    """
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
