from typing import List, Dict, Set

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.patches import Patch, Rectangle, Polygon
from matplotlib.text import Text
from matplotlib.lines import Line2D


ATTRIBUTES_TO_COPY = {
    Rectangle: {'_x0', '_y0', '_width', '_height'},
    Patch: {'_path', '_facecolor'},
    Polygon: {'xy', '_path'},
    Text: {'_text'},

    # need to copy '_invalidx', '_invalidy' because the new artists may not be valid (drawn) yet
    # this happens in the RectangleSelector
    Line2D: {'_xorig', '_yorig', '_x', '_y', '_xy', '_x_filled',
             '_path', '_transformed_path', '_invalidx', '_invalidy', '_visible'}
}


def get_attributes_to_copy(artist: Artist) -> Set[str]:
    return next((attributes for artist_type, attributes in ATTRIBUTES_TO_COPY.items()
                 if isinstance(artist, artist_type)),
                set())


def copy_attributes_from_new_to_previous_artists(previous_artists: List[Artist], new_artists: List[Artist]):
    # We only want to update from the new artists if their lengths are equal
    if len(new_artists) == len(previous_artists):
        for previous_artist, new_artist in zip(previous_artists, new_artists):
            for attribute in get_attributes_to_copy(previous_artist):
                setattr(previous_artist, attribute, getattr(new_artist, attribute))


def _update_drawing_order_of_created_artists(
        axes: Axes,
        new_artists: List[Artist],
        starting_index: int):
    """
    Updates the drawing order (layer) of the new artists according to the given previous starting index
    for a particular axes.
    """
    array = axes._children
    end_index = len(array) - len(new_artists)
    complete_artists_array = array[:starting_index] + new_artists + array[starting_index:end_index]
    axes._children = complete_artists_array


def update_new_artists_from_previous_artists(
        axeses_to_previous_indices: Dict[Axes, int],
        axeses_to_new_artists: Dict[Axes, List[Artist]]):
    """
    Updates the drawing order and attributes of the new artists from old ones
    """
    for axes, new_artists in axeses_to_new_artists.items():
        if axes in axeses_to_previous_indices:
            previous_index = axeses_to_previous_indices[axes]
            _update_drawing_order_of_created_artists(axes=axes,
                                                     new_artists=new_artists,
                                                     starting_index=previous_index)


def add_new_axesless_patches_to_axes(previous_artists: List[Artist], new_artists: List[Artist]):
    if len(new_artists) == len(previous_artists):
        for previous_artist, new_artist in zip(previous_artists, new_artists):
            if new_artist.axes is None and previous_artist.axes is not None \
                    and isinstance(new_artist, Patch) and isinstance(previous_artist, Patch):
                previous_artist.axes.add_patch(new_artist)
