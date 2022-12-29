import numpy as np
from matplotlib.backend_bases import PickEvent
from matplotlib.lines import Line2D


class ZeroDistance:
    def __next__(self):
        return [0, 0]

    def __iter__(self):
        return self


def _enhance_line2D_pick_event(pick_event: PickEvent):

    # TODO: may need to distinguish between segment picking and point picking.
    #  See the `contains` method of Line2D
    artist: Line2D = pick_event.artist
    xy_data = artist.get_xydata()
    ind = pick_event.ind
    mouseevent = pick_event.mouseevent
    pick_event.dxy = xy_data[ind, :] - [[mouseevent.xdata, mouseevent.ydata]]


ARTIST_TYPES_TO_REDUCE_FUNCTIONS = {
    Line2D: _enhance_line2D_pick_event,
}


def _enhance_pick_event(pick_event: PickEvent):
    """
    Store distance from mouse to picked points
    """
    reduce_function = ARTIST_TYPES_TO_REDUCE_FUNCTIONS.get(type(pick_event.artist), None)
    if reduce_function is None:
        try:
            ind = pick_event.ind
            pick_event.dxy = np.zeros(len(ind), 2)
        except (AttributeError, TypeError):
            pick_event.dxy = ZeroDistance()
    else:
        reduce_function(pick_event)
