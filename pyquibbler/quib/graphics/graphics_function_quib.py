import numpy as np
from contextlib import contextmanager
from typing import List, Callable, Tuple, Any, Mapping, Dict, Optional, Iterable, Set
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import Collection
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
from matplotlib.table import Table
from matplotlib.text import Text

from . import global_collecting
from .event_handling import CanvasEventHandler
from .quib_guard import QuibGuard
from ..assignment import AssignmentTemplate, PathComponent
from ..function_quibs import DefaultFunctionQuib, CacheBehavior
from ..utils import recursively_run_func_on_object, iter_object_type_in_args
from ...env import GRAPHICS_LAZY

Indices = Any
ArrayNameToArtists = Dict[str, List[Artist]]


def save_func_and_args_on_artists(artist: Artist, func: Callable, args: Iterable[Any]):
    """
    Set the drawing func and on the artist- this will be used later on when tracking an artist, in order to know how to
    inverse and handle events.
    If there's already a creating func, we assume the lower func that already created the artist is the actual
    drawing func (such as a user func that called plt.plot)
    """
    if getattr(artist, '_quibbler_drawing_func', None) is None:
        artist._quibbler_drawing_func = func
        artist._quibbler_args = args


class GraphicsFunctionQuib(DefaultFunctionQuib):
    """
    A function quib representing a function that can potentially draw graphics.
    This quib takes care of removing any previously drawn artists and updating newly created artists with old artist's
    attributes, such as color.
    """

    # Avoid unnecessary repaints
    _DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON

    TYPES_TO_ARTIST_ARRAY_NAMES = {
        Line2D: "lines",
        Collection: "collections",
        Patch: "patches",
        Text: "texts",
        Spine: "spines",
        Table: "tables",
        AxesImage: "images"
    }

    # Some attributes, like 'color', are chosen by matplotlib automatically if not specified.
    # Therefore, if these attributes were not specified, we need to copy them
    # from old artists to new artists.
    #
    # (attribute_to_copy_unless_included_in: {list of kwards})
    ATTRIBUTES_TO_COPY_FROM_ARTIST_TO_ARTIST_UNLESS_SPECIFED = {
        '_color': {'color'},
        '_facecolor': {'facecolor'},
    }

    # Note that this current implementation does not account for implicit color specification,
    # such as with plot(x,y,c), where c = iquib('r').
    # also it does not account for artiststs created within user-defined functions.

    def __init__(self,
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 artists: Iterable[Artist],
                 assignment_template: Optional[AssignmentTemplate] = None,
                 had_artists_on_last_run: bool = False,
                 receive_quibs: bool = False
                 ):
        super().__init__(func, args, kwargs, cache_behavior, assignment_template=assignment_template)
        self._artists_ndarr = np.array(set(artists))
        self._had_artists_on_last_run = had_artists_on_last_run
        self._receive_quibs = receive_quibs

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, lazy=None, **kwargs):
        self = super().create(func, func_args, func_kwargs, cache_behavior, artists=[], **kwargs)
        if lazy is None:
            lazy = GRAPHICS_LAZY
        if not lazy:
            self.get_value()
        return self

    def persist_self_on_artists(self, artists: Set[Artist]):
        """
        Persist self on all artists we're connected to, making sure we won't be garbage collected until they are
        off the screen
        We need to also go over args as there may be a situation in which the function did not create new artists, but
        did perform an action on an existing one, such as Axes.set_xlim
        """
        artists_to_persist_on = artists if artists else iter_object_type_in_args(Artist, self.args, self.kwargs)
        for artist in artists_to_persist_on:
            quibs = getattr(artist, '_quibbler_graphics_function_quibs', set())
            quibs.add(self)
            artist._quibbler_graphics_function_quibs = quibs

    def _get_artist_array_name(self, artist: Artist):
        return next((
            array_name
            for type_, array_name in self.TYPES_TO_ARTIST_ARRAY_NAMES.items()
            if isinstance(artist, type_)
        ), "artists")

    def _get_artist_array(self, artist: Artist):
        return getattr(artist.axes, self._get_artist_array_name(artist))

    def _get_axeses_to_array_names_to_artists(self, artists: Iterable[Artist]) -> Dict[Axes, ArrayNameToArtists]:
        """
        Creates a mapping of axes -> artist_array_name (e.g. `lines`) -> artists
        """
        axeses_to_array_names_to_artists = {}
        for artist in artists:
            array_names_to_artists = axeses_to_array_names_to_artists.setdefault(artist.axes, {})
            array_names_to_artists.setdefault(self._get_artist_array_name(artist), []).append(artist)
        return axeses_to_array_names_to_artists

    def _update_position_and_attributes_of_created_artists(
            self,
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
        end_index = len(array) - len(new_artists)
        complete_artists_array = array[:starting_index] + new_artists + array[starting_index:end_index]
        # insert new artists at correct location
        setattr(axes, array_name, complete_artists_array)
        # We only want to update from the previous artists if their lengths are equal (if so, we assume they're
        # referencing the same artists)
        if len(new_artists) == len(previous_artists):
            for previous_artist, new_artist in zip(previous_artists, new_artists):
                for attribute in self.ATTRIBUTES_TO_COPY_FROM_ARTIST_TO_ARTIST_UNLESS_SPECIFED.keys():
                    if hasattr(previous_artist, attribute) \
                            and not (self.kwargs.keys() &
                                     self.ATTRIBUTES_TO_COPY_FROM_ARTIST_TO_ARTIST_UNLESS_SPECIFED[attribute]):
                        setattr(new_artist, attribute, getattr(previous_artist, attribute))

    def _update_new_artists_from_previous_artists(self,
                                                  previous_axeses_to_array_names_to_indices_and_artists: Dict[
                                                      Axes, Dict[str, Tuple[int, List[Artist]]]
                                                  ],
                                                  current_axeses_to_array_names_to_artists: Dict[
                                                      Axes, ArrayNameToArtists
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

    def _get_args_for_call_with_quibs(self):
        proxy_quibs = set()

        def _replace_quibs_with_proxy_quibs(arg):
            from pyquibbler.quib import Quib, ProxyQuib
            if isinstance(arg, Quib):
                proxy_quib = ProxyQuib(quib=arg)
                proxy_quibs.add(proxy_quib)
                return proxy_quib
            return arg

        args = recursively_run_func_on_object(_replace_quibs_with_proxy_quibs, self.args)
        kwargs = {k: recursively_run_func_on_object(_replace_quibs_with_proxy_quibs, v) for k, v in self.kwargs.items()}
        return args, kwargs, proxy_quibs

    @contextmanager
    def _handle_new_artists(self, artist_set: Set[Artist]):
        self._remove_artists_that_were_removed_from_axes(artist_set)
        # Get the *current* artists together with their starting indices (per axes per artists array) so we can
        # place the new artists we create in their correct locations
        previous_axeses_to_array_names_to_indices_and_artists = \
            self._get_axeses_to_array_names_to_starting_indices_and_artists(artist_set)
        for artist in artist_set:
            self._remove_artist(artist)
        artist_set.clear()

        with global_collecting.ArtistsCollector() as collector:
            yield

        artist_set.update(collector.artists_collected)
        self._had_artists_on_last_run = len(artist_set) > 0

        for artist in artist_set:
            save_func_and_args_on_artists(artist, func=self.func, args=self.args)
            self.track_artist(artist)
        self.persist_self_on_artists(artist_set)

        current_axeses_to_array_names_to_artists = self._get_axeses_to_array_names_to_artists(artist_set)
        self._update_new_artists_from_previous_artists(previous_axeses_to_array_names_to_indices_and_artists,
                                                       current_axeses_to_array_names_to_artists)

    def _remove_artist(self, artist: Artist):
        """
        Remove an artist from its artist array (does NOT redraw)
        """
        self._get_artist_array(artist).remove(artist)

    def _get_axeses_to_array_names_to_starting_indices_and_artists(self, artists: Set[Artist]) \
            -> Dict[Axes, Dict[str, Tuple[int, List[Artist]]]]:
        """
        Creates a mapping of axes -> artists_array_name -> (starting_index, artists)
        """
        axeses_to_array_names_to_indices_and_artists = {}
        for axes, array_names_to_artists in self._get_axeses_to_array_names_to_artists(artists).items():
            array_names_to_indices_and_artists = {}
            axeses_to_array_names_to_indices_and_artists[axes] = array_names_to_indices_and_artists

            for array_name, array_artists in array_names_to_artists.items():
                exemplifying_artist = array_artists[0]
                array = getattr(exemplifying_artist.axes, array_name)
                array_names_to_indices_and_artists[array_name] = (array.index(exemplifying_artist), array_artists)

        return axeses_to_array_names_to_indices_and_artists

    def get_axeses(self) -> List[Axes]:
        artists = (artist for artists in self._artists_ndarr.flat for artist in artists)
        return list(self._get_axeses_to_array_names_to_artists(artists).keys())

    def track_artist(self, artist: Artist):
        CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)

    def _remove_artists_that_were_removed_from_axes(self, artist_set: Set[Artist]):
        """
        Remove any artists that we created that were removed by another means other than us (for example, cla())
        """
        artist_set.difference_update([artist for artist in artist_set if artist not in self._get_artist_array(artist)])

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        """
        Create the new artists, then update them (if appropriate) with correct attributes (such as color) and place them
        in the same place they were in their axes.
        Return the function's result.
        """
        assert self._artists_ndarr.ndim == 0
        artist_set = self._artists_ndarr[()]

        if self._receive_quibs:
            args, kwargs, quibs_for_guard = self._get_args_for_call_with_quibs()
        else:
            quibs_for_guard = self.parents
            args, kwargs = self._prepare_args_for_call(valid_path)

        with self._handle_new_artists(artist_set):
            with QuibGuard(quibs_for_guard):
                return self.func(*args, **kwargs)
