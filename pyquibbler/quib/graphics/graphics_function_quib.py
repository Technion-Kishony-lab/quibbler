from itertools import chain
from typing import List, Callable, Tuple, Any, Mapping, Dict, Optional

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
from ..assignment import AssignmentTemplate
from ..function_quibs import DefaultFunctionQuib, CacheBehavior
from ..utils import call_func_with_quib_values, iter_object_type_in_args


class GraphicsFunctionQuib(DefaultFunctionQuib):
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

    def __init__(self,
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 artists: List[Artist],
                 assignment_template: Optional[AssignmentTemplate] = None):
        super().__init__(func, args, kwargs, cache_behavior, assignment_template=assignment_template)
        self._artists = artists

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, lazy=False, **kwargs):
        self = super(GraphicsFunctionQuib, cls).create(func, func_args, func_kwargs, cache_behavior,
                                                       artists=[], **kwargs)
        if not lazy:
            self.get_value()
        return self

    def persist_self_on_artists(self):
        """
        Persist self on on all artists we're connected to, making sure we won't be garbage collected until they are
        off the screen
        We need to also go over args as there may be a situation in which the function did not create new artists, but
        did perform an action on an existing one, such as Axes.set_xlim
        """
        for artist in chain(self._artists, iter_object_type_in_args(Artist, self.args, self.kwargs)):
            quibs = getattr(artist, "graphics_function_quibs", set())
            quibs.add(self)
            artist.graphics_function_quibs = quibs

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
        for artist in self._artists:
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

        with global_collecting.global_graphics_collecting_mode():
            func_res = call_func_with_quib_values(self.func, self.args, self.kwargs)
        self._artists = global_collecting.get_artists_collected()
        self.persist_self_on_artists()
        self.track_artists()

        current_axeses_to_array_names_to_artists = self._get_axeses_to_array_names_to_artists()
        self._update_new_artists_from_previous_artists(previous_axeses_to_array_names_to_indices_and_artists,
                                                       current_axeses_to_array_names_to_artists)
        return func_res

    def _remove_current_artists(self):
        """
        Remove all the current artists (does NOT redraw)
        """
        for artist in self._artists:
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

    def track_artists(self):
        for artist in self._artists:
            CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)

    def _call_func(self):
        """
        The main entrypoint- this reruns the function that created the artists in the first place,
        and replaces the current artists with the new ones
        """

        # Get the *current* artists together with their starting indices (per axes per artists array) so we can
        # place the new artists we create in their correct locations
        axeses_to_array_names_to_indices_and_artists = self._get_axeses_to_array_names_to_starting_indices_and_artists()
        self._remove_current_artists()
        return self._create_new_artists(axeses_to_array_names_to_indices_and_artists)
