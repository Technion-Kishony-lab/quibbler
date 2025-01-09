from dataclasses import dataclass
from typing import Dict, Type, Literal

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from numpy.linalg import norm

from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.quib.types import PointArray
from pyquibbler.quib.graphics import artist_wrapper

from .utils import get_closest_point_on_line


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
    return [ind], xy_data, False


def _get_line2D_inds_xydata_segment(pick_event: PickEvent):
    """
    Get the picked vertices of a Line2D Artist and indicate whether picking a segment
    For now, we only support picking a single point or a single segment (so is_segment==len(inds)>1)
    """

    artist: Line2D = pick_event.artist
    xy_data = artist.get_xydata()
    inds = pick_event.ind

    if len(inds) > 1:
        # The mouse is close to multiple points, so pick the closest one:
        return _return_closest_point(pick_event, xy_data)
    elif len(inds) == 1:
        # matplotlib shows pick_event.ind with a single index even when picking a segment
        # so we need to check if this is a segment or a single point
        ind = inds[0]
        has_segments = artist._linestyle not in ['None', None]  # based on Line2D.contains()
        if has_segments and ind + 1 < len(xy_data):
            distance = _get_mouse_distance_to_points(artist.axes, pick_event.mouseevent, xy_data[ind:ind + 1, :])
            if distance > artist.get_pickradius():
                # not close to the picked point, so it is a segment
                return [ind, ind + 1], xy_data, True
        return [ind], xy_data, False
    else:
        assert False, 'Pick event has no indices'


def _get_PathCollection_inds_xydata_segment(pick_event: PickEvent):
    """
    Get the distance from the mouse to picked vertices of PathCollection Artist (acreated by plt.scatter)
    """
    artist: PathCollection = pick_event.artist
    xy_data = artist.get_offsets().data
    return _return_closest_point(pick_event, xy_data)


ARTIST_TYPES_TO_GET_XY_DATA: Dict[Type[Artist], callable] = {
    Line2D: _get_line2D_inds_xydata_segment,
    PathCollection: _get_PathCollection_inds_xydata_segment,
}


@dataclass
class EnhancedPickEvent:
    # original PickEvent attributes:
    ind: np.ndarray
    artist: Artist

    # new attributes:
    button: MouseButton | Literal["up", "down"] | None
    ax: Axes
    x: float
    y: float
    xy_offset: PointArray
    is_segment: bool
    mouse_to_segment: PointArray
    segment_fraction: float

    @classmethod
    def from_pick_event(cls, pick_event: PickEvent):
        mouseevent = pick_event.mouseevent
        artist = pick_event.artist

        # choose picked inds and add xy_offset, in pixels, from the mouse to each point:
        get_inds_xydata_segment = ARTIST_TYPES_TO_GET_XY_DATA.get(type(artist))
        ax = pick_event.artist.axes
        mouse_to_segment = None
        segment_fraction = None
        if get_inds_xydata_segment is None or mouseevent.xdata is None or mouseevent.ydata is None:
            ind = pick_event.ind
            xy_offset = np.zeros((1, 2))
            is_segment = False
        else:
            ind, xy_data, is_segment = get_inds_xydata_segment(pick_event)

            xy_data_pixels = ax.transData.transform(xy_data[ind, :])

            mouse_point = PointArray([mouseevent.x, mouseevent.y])
            if is_segment:
                on_segment_point, _ = get_closest_point_on_line(
                    PointArray(xy_data_pixels[0]), PointArray(xy_data_pixels[1]), mouse_point)
                xy_offset = xy_data_pixels - [on_segment_point]
                mouse_to_segment = on_segment_point - mouse_point
                segment_fraction = norm(on_segment_point - xy_data_pixels[0]) / norm(xy_data_pixels[1] - xy_data_pixels[0])

            else:
                xy_offset = xy_data_pixels - [mouse_point]

        return cls(
            ind=ind,
            artist=artist,
            button=mouseevent.button,
            ax=ax,
            x=mouseevent.x,
            y=mouseevent.y,
            xy_offset=xy_offset,
            is_segment=is_segment,
            mouse_to_segment=mouse_to_segment,
            segment_fraction=segment_fraction
        )


@dataclass
class EnhancedPickEventWithFuncArgsKwargs(EnhancedPickEvent):
    func_args_kwargs: FuncArgsKwargs = None

    @classmethod
    def from_pick_event(cls, pick_event: PickEvent):
        obj = super().from_pick_event(pick_event)
        obj.func_args_kwargs = artist_wrapper.get_creating_quib(obj.artist).handler.func_args_kwargs
        return obj
