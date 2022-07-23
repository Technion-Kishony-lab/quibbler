from typing import List, Dict, Tuple

from matplotlib.artist import Artist
from matplotlib.axes import Axes

from pyquibbler.graphics.utils import ArrayNameToArtists

ATTRIBUTES_TO_COPY = {}


def _copy_attributes_from_previous_to_new_artists(new_artists: List[Artist], previous_artists: List[Artist]):
    # Copy attributes from old to new artists
    # This functionality was used for copying auto-specified colors, which is not needed anymore as we are now using the
    # settable color cycler.
    # It is left here for now for possible future need.

    # We only want to update from the previous artists if their lengths are equal (if so, we assume they're
    # referencing the same artists)
    if len(new_artists) == len(previous_artists):
        for previous_artist, new_artist in zip(previous_artists, new_artists):
            for attribute in ATTRIBUTES_TO_COPY.keys():
                if hasattr(previous_artist, attribute):
                    setattr(new_artist, attribute, getattr(previous_artist, attribute))


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


def update_new_artists_from_previous_artists(previous_axeses_to_array_names_to_indices_and_artists: Dict[
                                                 Axes, Dict[str, Tuple[int, List[Artist]]]
                                             ],
                                             current_axeses_to_array_names_to_artists: Dict[
                                                 Axes, ArrayNameToArtists
                                             ],
                                             should_copy_artist_attributes):
    """
    Updates the drawing layer and attributes of the new artists from old ones
    """
    for axes, current_array_names_to_artists in current_axeses_to_array_names_to_artists.items():
        for array_name, artists in current_array_names_to_artists.items():
            if array_name in previous_axeses_to_array_names_to_indices_and_artists.get(axes, {}):
                array_names_to_indices_and_artists = previous_axeses_to_array_names_to_indices_and_artists[axes]
                starting_index, previous_artists = array_names_to_indices_and_artists[array_name]
                _update_drawing_order_of_created_artists(axes=axes,
                                                         array_name=array_name,
                                                         new_artists=artists,
                                                         starting_index=starting_index)
                if should_copy_artist_attributes:
                    _copy_attributes_from_previous_to_new_artists(artists, previous_artists)

            # Else, if the array name isn't in previous_array_names_to_indices_and_artists,
            # we don't need to update drawing order, or copy attributes
