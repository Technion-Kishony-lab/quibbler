from dataclasses import dataclass
from typing import Callable, Tuple, Any, Mapping, List, Set, Optional, Dict
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
from matplotlib.table import Table
from matplotlib.text import Text
from matplotlib.image import AxesImage

from pyquibbler.quib.utils import call_func_with_quib_values
from matplotlib.artist import Artist


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


class ArtistsRedrawer:
    """
    Handles redrawing artists in an efficient manner while keeping their position within the axes, as well as other 
    critical attributes (color etc)
    """

    TYPES_TO_ARTIST_ARRAY_NAMES = {
        Line2D: "lines",
        Collection: "collections",
        Patch: "patches",
        Text: "texts",
        Spine: "spines",
        Table: "tables",
        AxesImage: "images"
    }

    def __init__(self,
                 artists: List[Artist],
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any]):
        self.artists = artists
        self._func = func
        self._args = args
        self._kwargs = kwargs

    @classmethod
    def create_from_function_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
        artists = call_func_with_quib_values(func, args, kwargs)
        return cls(artists, func, args, kwargs)

    def _get_artist_array_name(self, artist: Artist):
        return next((
            array_name
            for type_, array_name in self.TYPES_TO_ARTIST_ARRAY_NAMES.items()
            if isinstance(artist, type_)
        ), "artists")

    def _get_artist_array(self, artist: Artist):
        return getattr(artist.axes, self._get_artist_array_name(artist))

    def _get_axeses_to_array_names_to_artists(self) -> Dict[Axes, Dict[str, List[Artist]]]:
        """
        Creates a mapping of axes -> artist_array_name (e.g. `lines`) -> artists
        """
        axeses_to_array_names_to_artists = {}
        for artist in self.artists:
            array_names_to_artists = axeses_to_array_names_to_artists.setdefault(artist.axes, {})
            array_names_to_artists.setdefault(self._get_artist_array_name(artist), []).append(artist)
        return axeses_to_array_names_to_artists

    @staticmethod
    def _update_position_and_attributes_of_created_artists(
            axes: Axes,
            array_name: str,
            new_artists: List[Artist],
            previous_artists: List[Artist],
            starting_index: int):
        """
        Updates the positions and attributes of the new artists from old ones (together with the given starting index)
        for a particular axes and array name
        """
        array = getattr(axes, array_name)
        complete_artists_array = array[:starting_index] + new_artists + array[starting_index:len(array)
                                                                                             - len(new_artists)]
        # insert new artists at correct location
        setattr(axes, array_name, complete_artists_array)
        # We only want to update from the previous artists if their lengths are equal (if so, we assume they're
        # referencing the same artists)
        if len(new_artists) == len(previous_artists):
            for previous_artist, new_artist in zip(previous_artists, new_artists):
                new_artist.update_from(previous_artist)

    def _update_new_artists_from_previous_artists(self,
                                                  previous_axeses_to_array_names_to_indices_and_artists: Dict[
                                                      Axes, Dict[str, Tuple[int, List[Artist]]]
                                                  ],
                                                  current_axeses_to_array_names_to_artists: Dict[
                                                      Axes, Dict[str, List[Artist]]
                                                  ]):
        """
        Updates the positions and attributes of the new artists from old ones
        """
        for axes, current_array_names_to_artists in current_axeses_to_array_names_to_artists.items():
            for array_name, artists in current_array_names_to_artists.items():
                if array_name in previous_axeses_to_array_names_to_indices_and_artists.get(axes, {}):
                    array_names_to_indices_and_artists = previous_axeses_to_array_names_to_indices_and_artists[axes]
                    starting_index, previous_artists = array_names_to_indices_and_artists[array_name]
                    self._update_position_and_attributes_of_created_artists(
                        axes=axes,
                        array_name=array_name,
                        new_artists=artists,
                        previous_artists=previous_artists,
                        starting_index=starting_index)
                # If the array name isn't in previous_array_names_to_indices_and_artists,
                # we don't need to update positions, etc

    def _create_new_artists(self,
                            previous_axeses_to_array_names_to_indices_and_artists:
                           Dict[Axes, Dict[str, Tuple[int, List[Artist]]]] = None):
        """
        Create the new artists, then update them (if appropriate) with correct attributes (such as color) and place them
        in the same place they were in their axes
        """
        previous_axeses_to_array_names_to_indices_and_artists = \
            previous_axeses_to_array_names_to_indices_and_artists or {}

        new_artists: List[Artist] = call_func_with_quib_values(self._func, self._args, self._kwargs)
        if isinstance(new_artists, Artist):
            new_artists = [new_artists]
        self.artists = new_artists

        current_axeses_to_array_names_to_artists = self._get_axeses_to_array_names_to_artists()
        self._update_new_artists_from_previous_artists(previous_axeses_to_array_names_to_indices_and_artists,
                                                       current_axeses_to_array_names_to_artists)

    def _remove_current_artists(self):
        """
        Remove all the current artists (does NOT redraw)
        """
        for artist in self.artists:
            self._get_artist_array(artist).remove(artist)

    def _get_axeses_to_array_names_to_starting_indices_and_artists(self) -> Dict[
        Axes, Dict[str, Tuple[int, List[Artist]]]
    ]:
        """
        Creates a mapping of axes -> artists_array_name -> (starting_index, artists)
        """
        axeses_to_array_names_to_indices_and_artists = {}
        for axes, array_names_to_artists in self._get_axeses_to_array_names_to_artists().items():
            array_names_to_indices_and_artists = {}
            axeses_to_array_names_to_indices_and_artists[axes] = array_names_to_indices_and_artists

            for array_name, artists in array_names_to_artists.items():
                exemplifying_artist = artists[0]
                array = getattr(exemplifying_artist.axes, array_name)
                array_names_to_indices_and_artists[array_name] = (array.index(exemplifying_artist), artists)
        return axeses_to_array_names_to_indices_and_artists

    def get_axeses(self) -> List[Axes]:
        return list(self._get_axeses_to_array_names_to_artists().keys())

    def redraw_axeses_and_update_gui(self):
        """
        Does the actual redrawing gui-wise - this should be WITHOUT rendering anything except for the new artists
        """
        for axes in self.get_axeses():
            redraw_axes(axes)

    def redraw(self, redraw_in_gui: bool = True):
        """
        The main entrypoint- this reruns the function that created the artists in the first place,
        and replaces the current artists with the new ones
        """

        # Get the *current* artists together with their starting indices (per axes per artists array) so we can
        # place the new artists we create in their correct locations
        axeses_to_array_names_to_indices_and_artists = self._get_axeses_to_array_names_to_starting_indices_and_artists()

        self._remove_current_artists()
        self._create_new_artists(axeses_to_array_names_to_indices_and_artists)

        if redraw_in_gui:
            self.redraw_axeses_and_update_gui()
