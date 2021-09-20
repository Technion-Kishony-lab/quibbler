from dataclasses import dataclass
from typing import Callable, Tuple, Any, Mapping, List, Set, Optional, Dict

from matplotlib.axes import Axes
from matplotlib.collections import Collection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
from matplotlib.table import Table
from matplotlib.text import Text
from matplotlib.image import AxesImage

from pyquibbler.env import is_debug
from pyquibbler.exceptions import DebugException
from pyquibbler.quib.utils import call_func_with_quib_values
from matplotlib.artist import Artist


class ArtistsRedrawer:
    """
    Handles redrawing artists in an efficient manner while keeping their position within the axes, as well as other 
    critical attributes (color etc)

    An ArtistsRedrawer MUST BE per one axes
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

    def _get_axes_array_names_to_artists(self) -> Dict[str, List[Artist]]:
        array_names_to_artists = {}
        for artist in self.artists:
            array_name = self._get_artist_array_name(artist)
            if array_name not in array_names_to_artists:
                array_names_to_artists[array_name] = []
            array_names_to_artists[array_name].append(artist)

        return array_names_to_artists

    def remove_current_artists(self):
        """
        Remove all the current artists (does NOT redraw)
        """
        for artist in self.artists:
            self._get_artist_array(artist).remove(artist)

    def redraw_axes_and_update_gui(self):
        """
        Does the actual redrawing gui-wise - this should be WITHOUT rendering anything except for the new artists
        """
        exemplifying_artist = self.artists[0]
        axes = exemplifying_artist.axes
        # if the renderer cache is None, we've never done an initial draw- which means we can just wait for the
        # initial draw to happen which will naturally use our updated artists
        if axes.get_renderer_cache() is not None:
            # redraw_in_frame is supposed to be a quick way to redraw all artists in an axes- the expectation is
            # that the renderer will not rerender any artists that already exist.
            # We saw that the performance matched the performance of what automatically happens when pausing
            # (which causes a the event loop to run)
            axes.redraw_in_frame()
            # After redrawing to the canvas, we now need to blit the bitmap to the GUI
            axes.figure.canvas.blit(axes.bbox)

    def create_new_artists(self,
                           previous_array_names_to_indices_and_artists: Dict[str, Tuple[int, List[Artist]]] = None):
        """
        Create the new artists in the correct index with
        """
        previous_array_names_to_indices_and_artists = previous_array_names_to_indices_and_artists or {}

        new_artists: List[Artist] = call_func_with_quib_values(self._func, self._args, self._kwargs)
        self.artists = new_artists

        current_array_names_to_artists = self._get_axes_array_names_to_artists()

        for array_name, artists in current_array_names_to_artists.items():
            if array_name in previous_array_names_to_indices_and_artists:
                starting_index, previous_artists = previous_array_names_to_indices_and_artists[array_name]

                exemplifying_artist = artists[0]
                array = getattr(exemplifying_artist.axes, array_name)
                complete_artists_array = array[:starting_index] + new_artists + array[starting_index:len(array)
                                                                                                     - len(new_artists)]

                # insert new artists at correct location
                setattr(exemplifying_artist.axes, array_name, complete_artists_array)

                # We only want to update from the previous artists if their lengths are equal (if so, we assume they're
                # referencing the same artists)
                if len(artists) == len(previous_artists):
                    for previous_artist, new_artist in zip(previous_artists, artists):
                        new_artist.update_from(previous_artist)
            # If the array name isn't in previous_array_names_to_indices_and_artists, we don't need to update positions,
            # etc

    def redraw(self):
        """
        The main entrypoint- this reruns the function that created the artists in the first place,
        and replaces the current artists with the new ones
        """
        if is_debug():
            axeses: Set[Axes] = set()
            for artist in self.artists:
                axeses.add(artist.axes)
            if len(axeses) > 1:
                raise DebugException("There cannot be more than one axes!")

        array_names_to_artists = self._get_axes_array_names_to_artists()
        axes_array_names_to_indices_and_artists = {}
        for array_name, artists in array_names_to_artists.items():
            exemplifying_artist = artists[0]
            array = getattr(exemplifying_artist.axes, array_name)
            axes_array_names_to_indices_and_artists[array_name] = (array.index(exemplifying_artist), artists)

        self.remove_current_artists()
        self.create_new_artists(axes_array_names_to_indices_and_artists)

        self.redraw_axes_and_update_gui()

