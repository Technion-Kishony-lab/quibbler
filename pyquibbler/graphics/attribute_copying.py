from typing import List, Dict, Tuple, Set

from matplotlib.artist import Artist
from matplotlib.axes import Axes

from pyquibbler.graphics.utils import ArrayNameToArtists

# Some attributes, like 'color', are chosen by matplotlib automatically if not specified.
# Therefore, if these attributes were not specified, we need to copy them
# from old artists to new artists.
#
# (attribute_to_copy_unless_included_in: {list of kwards})
ATTRIBUTES_TO_COPY_UNLESS_IN_KWARGS = {
    '_color': {'color'},
    '_facecolor': {'facecolor'},
}


def _copy_attributes(kwargs_specified_in_artists_creation: Set[str],
                     new_artists: List[Artist], previous_artists: List[Artist]):
    # We only want to update from the previous artists if their lengths are equal (if so, we assume they're
    # referencing the same artists)
    if len(new_artists) == len(previous_artists):
        for previous_artist, new_artist in zip(previous_artists, new_artists):
            for attribute in ATTRIBUTES_TO_COPY_UNLESS_IN_KWARGS.keys():
                if hasattr(previous_artist, attribute) and \
                        not (kwargs_specified_in_artists_creation & ATTRIBUTES_TO_COPY_UNLESS_IN_KWARGS[attribute]):
                    setattr(new_artist, attribute, getattr(previous_artist, attribute))


def _update_position_and_attributes_of_created_artists(
        kwargs_specified_in_artists_creation: Set[str],
        axes: Axes,
        array_name: str,
        new_artists: List[Artist],
        previous_artists: List[Artist],
        starting_index: int,
        should_copy_artist_attributes: bool):
    """
    Updates the positions and attributes of the new artists from old ones (together with the given starting index)
    for a particular axes and array name
    """
    array = getattr(axes, array_name)
    end_index = len(array) - len(new_artists)
    complete_artists_array = array[:starting_index] + new_artists + array[starting_index:end_index]
    # insert new artists at correct location
    setattr(axes, array_name, complete_artists_array)

    if should_copy_artist_attributes:
        _copy_attributes(kwargs_specified_in_artists_creation, new_artists, previous_artists)


def update_new_artists_from_previous_artists(kwargs_specified_in_artists_creation: Set[str],
                                              previous_axeses_to_array_names_to_indices_and_artists: Dict[
                                                  Axes, Dict[str, Tuple[int, List[Artist]]]
                                              ],
                                              current_axeses_to_array_names_to_artists: Dict[
                                                  Axes, ArrayNameToArtists
                                              ],
                                              should_copy_artist_attributes):
    """
    Updates the positions and attributes of the new artists from old ones
    """
    for axes, current_array_names_to_artists in current_axeses_to_array_names_to_artists.items():
        for array_name, artists in current_array_names_to_artists.items():
            if array_name in previous_axeses_to_array_names_to_indices_and_artists.get(axes, {}):
                array_names_to_indices_and_artists = previous_axeses_to_array_names_to_indices_and_artists[axes]
                starting_index, previous_artists = array_names_to_indices_and_artists[array_name]
                _update_position_and_attributes_of_created_artists(
                    kwargs_specified_in_artists_creation,
                    axes=axes,
                    array_name=array_name,
                    new_artists=artists,
                    previous_artists=previous_artists,
                    starting_index=starting_index,
                    should_copy_artist_attributes=should_copy_artist_attributes)
            # If the array name isn't in previous_array_names_to_indices_and_artists,
            # we don't need to update positions, etc
