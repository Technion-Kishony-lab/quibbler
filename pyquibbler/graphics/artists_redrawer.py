import time
from typing import Callable, Tuple, Any, Mapping, List, Set

from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from pyquibbler.env import is_debug
from pyquibbler.exceptions import DebugException
from pyquibbler.quib.utils import iter_quibs_in_args, call_func_with_quib_values
from matplotlib.artist import Artist
from matplotlib import pyplot as plt


class ArtistsRedrawer:
    """
    Handles redrawing artists in an efficient manner while keeping their position within the axes, as well as other 
    critical attributes (color etc)
    """

    TYPES_TO_ARTIST_ARRAY_NAMES = {
        Line2D: "lines"
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

    @property
    def _exemplifying_artist(self) -> Artist:
        """
        We expect certain attributes of our artists (for example their `axes`, `zorder`, type)
        to be the same in all our artists-
        (Based on the assumption that one matplotlib function won't output artists with different attributes in
        above areas)
        This means we can take the first artist as an "exemplifying" artist for certain attributes
        """
        return self.artists[0]

    @property
    def _axes(self) -> Axes:
        return self._exemplifying_artist.axes

    @property
    def _artists_array_name(self) -> str:
        """
        The name of the array within `self._axes` that the artists belongs to
        """
        # TODO: check if doesn't exist
        return self.TYPES_TO_ARTIST_ARRAY_NAMES[self._exemplifying_artist.__class__]

    @property
    def _artists_array(self) -> List[Artist]:
        """
        The array within `self._axes` that the artists belongs to
        """
        return getattr(self._axes, self._artists_array_name)

    def _remove_current_artists(self):
        """
        Remove all the current artists
        """
        for artist in self.artists:
            self._artists_array.remove(artist)

    def _create_new_artists(self, previous_artists_index: int, previous_exemplifying_artist: Artist):
        """
        Create the new artists in the correct index with
        """
        new_artists = call_func_with_quib_values(self._func, self._args, self._kwargs)
        self.artists = new_artists

        # insert new artists at correct location
        complete_artists_array = self._artists_array[:previous_artists_index] + new_artists + \
                                 self._artists_array[previous_artists_index:len(self._artists_array) - len(new_artists)]
        setattr(self._axes, self._artists_array_name, complete_artists_array)

        for new_artist in new_artists:
            new_artist.zorder = previous_exemplifying_artist.zorder
            new_artist.set_color(previous_exemplifying_artist.get_color())

    def _redraw_axes_and_update_gui(self):
        """
        Does the actual redrawing gui-wise - this should be WITHOUT rendering anything except for the new artists
        """
        # if the renderer cache is None, we've never done an initial draw- which means we can just wait for the
        # initial draw to happen which will naturally use our updated artists
        if self._axes.get_renderer_cache() is not None:
            # redraw_in_frame is supposed to be a quick way to redraw all artists in an axes- the expectation is
            # that the renderer will not rerender any artists that already exist.
            # We saw that the performance matched the performance of what automatically happens when pausing
            # (which causes a redraw)
            self._axes.redraw_in_frame()
            self._axes.figure.canvas.blit(self._axes.bbox)

    def redraw(self):
        """
        The main entrypoint- this reruns the function that created the artists in the first place,
        and replaces the current artists with the new ones
        """
        # TODO use update_from
        # COLOR
        if is_debug():
            axeses: Set[Axes] = set()
            for artist in self.artists:
                axeses.add(artist.axes)
            if len(axeses) > 1:
                raise DebugException("There cannot be more than one axes!")

        previous_artists_index = self._artists_array.index(self._exemplifying_artist)
        previous_exemplifying_artist = self._exemplifying_artist
        self._remove_current_artists()
        self._create_new_artists(previous_exemplifying_artist=previous_exemplifying_artist,
                                 previous_artists_index=previous_artists_index)

        self._redraw_axes_and_update_gui()


def override_axes_method(method_name: str):
    """
    Override an axes method to create a method that will add an artistsredrawer to any quibs in the arguments

    :param method_name - name of axes method
    """
    cls = plt.Axes
    original_method = getattr(cls, method_name)

    def override(*args, **kwargs):
        redrawer = ArtistsRedrawer.create_from_function_call(
            func=original_method,
            args=args,
            kwargs=kwargs
        )
        for quib in iter_quibs_in_args(args, kwargs):
            quib.add_artists_redrawer(redrawer)

        return redrawer.artists

    setattr(cls, method_name, override)


OVERRIDDEN_AXES_METHODS = ['plot', 'imshow', 'text']


def override_axes_methods():
    """
    Override all axes methods so we can add redrawers to the relevant quibs
    """
    for axes_method in OVERRIDDEN_AXES_METHODS:
        override_axes_method(axes_method)
