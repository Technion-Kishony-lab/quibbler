import numpy as np
from matplotlib.backend_bases import PickEvent
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D


class ZeroDistance:
    def __next__(self):
        return [0, 0]

    def __iter__(self):
        return self


def _get_line2D_xy_data(pick_event: PickEvent):
    """
    Get the distance from the mouse to picked vertices of Line2D Artist
    """
    # TODO: may need to distinguish between segment picking and point picking.
    #  See the `contains` method of Line2D
    artist: Line2D = pick_event.artist
    return artist.get_xydata()


def _get_PathCollection_xy_data(pick_event: PickEvent):
    """
    Get the distance from the mouse to picked vertices of PathCollection Artist (acreated by plt.scatter)
    """
    artist: PathCollection = pick_event.artist
    return artist.get_offsets().data


ARTIST_TYPES_TO_GET_XY_DATA = {
    Line2D: _get_line2D_xy_data,
    PathCollection: _get_PathCollection_xy_data,
}


def _enhance_pick_event(pick_event: PickEvent):
    """
    Store distance from mouse to picked points
    """
    get_xy_data = ARTIST_TYPES_TO_GET_XY_DATA.get(type(pick_event.artist), None)
    if get_xy_data is None:
        try:
            ind = pick_event.ind
            pick_event.dxy = np.zeros(len(ind), 2)
        except (AttributeError, TypeError):
            pick_event.dxy = ZeroDistance()
    else:
        xy_data = get_xy_data(pick_event)
        ind = pick_event.ind
        mouseevent = pick_event.mouseevent
        pick_event.dxy = xy_data[ind, :] - [[mouseevent.xdata, mouseevent.ydata]]
