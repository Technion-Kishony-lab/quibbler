from typing import Tuple

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import PickEvent, MouseEvent
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D

from pyquibbler.quib.types import PointXY

from .utils import get_closest_point_on_line

Inds = Tuple[int]


class ZeroDistance:
    def __next__(self):
        return [0, 0]

    def __iter__(self):
        return self


def _get_mouse_distance_to_points(ax: Axes, mouseevent: MouseEvent, xy_data):
    """
    Return the distances of the mouse, in pixels, from each of the data point xy_data (array of Nx2)
    """
    xy_pixels = ax.transData.transform(xy_data)
    xy_pick_event_pixels = [mouseevent.x, mouseevent.y]
    dxy = xy_pixels - [xy_pick_event_pixels]
    return np.sqrt(np.sum(np.square(dxy), axis=1))


def _return_closest_point(pick_event: PickEvent, xy_data):
    """
    Pick the closest point to the mouse
    """
    inds = pick_event.ind
    distances = _get_mouse_distance_to_points(pick_event.artist.axes, pick_event.mouseevent, xy_data[inds, :])
    ind = inds[np.argmin(distances)]
    inds = (ind,)
    return inds, xy_data, False


def _get_line2D_inds_xydata_segment(pick_event: PickEvent):
    """
    Get the picked vertices of a Line2D Artist and indicate whether picking a segment
    """

    artist: Line2D = pick_event.artist
    xy_data = artist.get_xydata()
    inds = pick_event.ind

    # based on Line2D.contains():
    is_segment = artist._linestyle not in ['None', None]

    if is_segment:
        ind = inds[0]  # TODO: get the closest segment
        is_segment = ind + 1 < len(artist.get_xydata())
        if is_segment:
            distances = _get_mouse_distance_to_points(artist.axes, pick_event.mouseevent, xy_data[ind:ind+2, :])
            ind_closest = np.argmin(distances)
            ind_farthest = 1 - ind_closest
            is_segment = not (distances[ind_farthest] > artist.get_pickradius()
                              and distances[ind_closest] / distances[ind_farthest] < 0.1)
            if not is_segment:
                ind = ind + ind_closest
    else:
        return _return_closest_point(pick_event, xy_data)

    if is_segment:
        inds = (ind, ind + 1)
    else:
        inds = (ind, )

    return inds, xy_data, is_segment


def _get_PathCollection_inds_xydata_segment(pick_event: PickEvent):
    """
    Get the distance from the mouse to picked vertices of PathCollection Artist (acreated by plt.scatter)
    """
    artist: PathCollection = pick_event.artist
    xy_data = artist.get_offsets().data
    return _return_closest_point(pick_event, xy_data)


ARTIST_TYPES_TO_GET_XY_DATA = {
    Line2D: _get_line2D_inds_xydata_segment,
    PathCollection: _get_PathCollection_inds_xydata_segment,
}


def enhance_pick_event(pick_event: PickEvent):
    """
    Choose which points or line segments were picked and store offset from mouse to picked points
    """

    mouseevent = pick_event.mouseevent

    # choose picked inds and add xy_offset, in pixels, from the mouse to each point:
    get_inds_xydata_segment = ARTIST_TYPES_TO_GET_XY_DATA.get(type(pick_event.artist), None)
    ax = pick_event.artist.axes

    if get_inds_xydata_segment is None or mouseevent.xdata is None or mouseevent.ydata is None:
        try:
            ind = pick_event.ind
            pick_event.xy_offset = np.zeros(len(ind), 2)
        except (AttributeError, TypeError):
            pick_event.xy_offset = ZeroDistance()
        pick_event.is_segment = False
    else:

        inds, xy_data, is_segment = get_inds_xydata_segment(pick_event)

        xy_data_pixels = ax.transData.transform(xy_data[inds, :])
        pick_event.ind = inds

        pick_event.is_segment = is_segment

        mouse_point = PointXY(mouseevent.x, mouseevent.y)
        if is_segment:
            on_segment_point, _ = get_closest_point_on_line(
                PointXY(*xy_data_pixels[0]), PointXY(*xy_data_pixels[1]), mouse_point)
            pick_event.xy_offset = xy_data_pixels - [on_segment_point]
            pick_event.mouse_to_segment = on_segment_point - mouse_point
        else:
            pick_event.xy_offset = xy_data_pixels - [mouse_point]

    # add picked position in pixels:
    pick_event.x = mouseevent.x
    pick_event.y = mouseevent.y
