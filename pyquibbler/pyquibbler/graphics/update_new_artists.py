from typing import List, Dict, Set

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Text
from matplotlib.lines import Line2D

from pyquibbler.graphics.utils import ArrayNameToArtists

ATTRIBUTES_TO_COPY = {
    Rectangle: {'_x0', '_y0', '_width', '_height'},
    Patch: {'_path'},
    Text: {'_text'},

    # need to copy '_invalidx', '_invalidy' because the new artists may not be valid (drawn) yet
    # this happens in the RectangleSelector
    Line2D: {'_xorig', '_yorig', '_x', '_y', '_xy', '_x_filled',
             '_path', '_transformed_path', '_invalidx', '_invalidy'}
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
        array_name: str,
        new_artists: List[Artist],
        starting_index: int):
    """
    Updates the drawing order (layer) of the new artists according to the given previous starting index
    for a particular axes and array name.
    """
    array = getattr(axes, array_name)
    end_index = len(array) - len(new_artists)
    complete_artists_array = array[:starting_index] + new_artists + array[starting_index:end_index]

    setattr(axes, array_name, complete_artists_array)   # insert new artists at previous drawing order


def update_new_artists_from_previous_artists(
        previous_axeses_to_array_names_to_indices: Dict[Axes, Dict[str, int]],
        current_axeses_to_array_names_to_artists: Dict[Axes, ArrayNameToArtists]):
    """
    Updates the drawing order and attributes of the new artists from old ones
    """
    for axes, current_array_names_to_artists in current_axeses_to_array_names_to_artists.items():
        for array_name, artists in current_array_names_to_artists.items():
            if array_name in previous_axeses_to_array_names_to_indices.get(axes, {}):
                array_names_to_indices = previous_axeses_to_array_names_to_indices[axes]
                starting_index = array_names_to_indices[array_name]
                _update_drawing_order_of_created_artists(axes=axes,
                                                         array_name=array_name,
                                                         new_artists=artists,
                                                         starting_index=starting_index)

            # Else, if the array name isn't in previous_array_names_to_indices_and_artists,
            # we don't need to update drawing order, or copy attributes


def add_new_axesless_patches_to_axes(previous_artists: List[Artist], new_artists: List[Artist]):
    if len(new_artists) == len(previous_artists):
        for previous_artist, new_artist in zip(previous_artists, new_artists):
            if new_artist.axes is None and previous_artist.axes is not None \
                    and isinstance(new_artist, Patch) and isinstance(previous_artist, Patch):
                previous_artist.axes.add_patch(new_artist)
