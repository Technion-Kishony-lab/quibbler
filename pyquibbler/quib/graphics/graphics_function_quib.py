import numpy as np
from contextlib import contextmanager
from typing import List, Callable, Tuple, Any, Mapping, Dict, Optional, Iterable, Set, Union
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.widgets import AxesWidget

from .global_collecting import ArtistsCollector, AxesWidgetsCollector
from .graphics_collection import GraphicsCollection
from .quib_guard import QuibGuard
from .update_type import UpdateType
from .utils import save_func_and_args_on_artists, get_axeses_to_array_names_to_starting_indices_and_artists, \
    remove_artist, get_axeses_to_array_names_to_artists, get_artist_array, ArrayNameToArtists, track_artist
from .widget_utils import destroy_widgets, transfer_data_from_new_widgets_to_previous_widgets, \
    update_previous_widget_from_new_widget
from ..assignment import AssignmentTemplate, PathComponent
from ..function_quibs import DefaultFunctionQuib, CacheBehavior
from ..function_quibs.external_call_failed_exception_handling import external_call_failed_exception_handling
from ..utils import recursively_run_func_on_object, iter_object_type_in_args, iter_quibs_in_args
from ...env import GRAPHICS_EVALUATE_NOW
from ...input_validation_utils import InvalidArgumentException


def create_array_from_func(func, shape):
    return np.vectorize(lambda _: func(), otypes=[object])(np.empty(shape))


def proxify_args(args, kwargs):
    from pyquibbler.quib import Quib, ProxyQuib
    replace_quibs_with_proxy_quibs = lambda arg: ProxyQuib(arg) if isinstance(arg, Quib) else arg
    args = recursively_run_func_on_object(replace_quibs_with_proxy_quibs, args)
    kwargs = {k: recursively_run_func_on_object(replace_quibs_with_proxy_quibs, v) for k, v in kwargs.items()}
    return args, kwargs


class GraphicsFunctionQuib(DefaultFunctionQuib):
    """
    A function quib representing a function that can potentially draw graphics.
    This quib takes care of removing any previously drawn artists and updating newly created artists with old artist's
    attributes, such as color.
    """

    _DEFAULT_EVALUATE_NOW = GRAPHICS_EVALUATE_NOW

    _DEFAULT_REDRAW_UPDATE_TYPE = UpdateType.DRAG

    # Avoid unnecessary repaints
    _DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON

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
                 assignment_template: Optional[AssignmentTemplate] = None,
                 had_artists_on_last_run: bool = False,
                 pass_quibs: bool = False,
                 update_type: UpdateType = None):
        super().__init__(func, args, kwargs, cache_behavior, assignment_template)
        self._had_artists_on_last_run = had_artists_on_last_run
        self._pass_quibs = pass_quibs
        self._graphics_collection_ndarr = None
        self.update_type = update_type or UpdateType.DRAG

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None,
               update_type: Union[UpdateType, str] = None, evaluate_now: bool = None, **init_kwargs):
        update_type = update_type or cls._DEFAULT_REDRAW_UPDATE_TYPE
        if isinstance(update_type, str):
            try:
                update_type = UpdateType[update_type.upper()]
            except KeyError:
                raise InvalidArgumentException(var_name="updated_type", expected_type=UpdateType) from None
        self = super(GraphicsFunctionQuib, cls).create(func=func, func_args=func_args, func_kwargs=func_kwargs,
                                                       cache_behavior=cache_behavior, update_type=update_type,
                                                       **init_kwargs)

        if evaluate_now is None:
            evaluate_now = cls._DEFAULT_EVALUATE_NOW

        if evaluate_now:
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

    def _remove_artists(self, artist_set: Set[Artist]):
        for artist in artist_set:
            remove_artist(artist)
        artist_set.clear()

    def _remove_artists_that_were_removed_from_axes(self, artist_set: Set[Artist]):
        """
        Remove any artists that we created that were removed by another means other than us (for example, cla())
        """
        artist_set.difference_update([artist for artist in artist_set if artist not in get_artist_array(artist)])

    def _iter_artist_sets(self) -> Iterable[Set[Artist]]:
        return [] if self._graphics_collection_ndarr is None else map(lambda g: g.artists,
                                                                      self._graphics_collection_ndarr.flat)

    def _iter_widget_sets(self) -> Iterable[Set[AxesWidget]]:
        return [] if self._graphics_collection_ndarr is None else map(lambda g: g.widgets,
                                                                      self._graphics_collection_ndarr.flat)

    def _iter_artists(self) -> Iterable[Artist]:
        return (artist for artists in self._iter_artist_sets() for artist in artists)

    def get_axeses(self) -> Set[Axes]:
        return {artist.axes for artist in self._iter_artists()}

    def _get_loop_shape(self) -> Tuple[int, ...]:
        return ()

    def _initialize_graphics_ndarr(self):
        loop_shape = self._get_loop_shape()
        if self._graphics_collection_ndarr is not None and self._graphics_collection_ndarr.shape != loop_shape:
            for artist_set in self._iter_artist_sets():
                self._remove_artists(artist_set)
            self._graphics_collection_ndarr = None
        if self._graphics_collection_ndarr is None:
            self._graphics_collection_ndarr = create_array_from_func(GraphicsCollection, loop_shape)

    def _run_single_call(self, func, graphics_collection: GraphicsCollection, args, kwargs):
        self._remove_artists_that_were_removed_from_axes(graphics_collection.artists)
        # Get the *current* artists together with their starting indices (per axes per artists array) so we can
        # place the new artists we create in their correct locations
        previous_axeses_to_array_names_to_indices_and_artists = \
            get_axeses_to_array_names_to_starting_indices_and_artists(graphics_collection.artists)
        self._remove_artists(graphics_collection.artists)

        with ArtistsCollector() as artists_collector, AxesWidgetsCollector() as widgets_collector, \
                external_call_failed_exception_handling(), QuibGuard(set(iter_quibs_in_args(self.args, self.kwargs))):
            ret_val = func(*args, **kwargs)

        graphics_collection.artists.update(artists_collector.objects_collected)
        if len(graphics_collection.widgets) > 0:

            if isinstance(ret_val, AxesWidget):
                assert len(widgets_collector.objects_collected) == 1
                assert len(graphics_collection.widgets) == 1
                ret_val = list(graphics_collection.widgets)[0]

            destroy_widgets(widgets_collector.objects_collected)
            transfer_data_from_new_widgets_to_previous_widgets(previous_widgets=graphics_collection.widgets,
                                                               new_widgets=widgets_collector.objects_collected)
        else:
            graphics_collection.widgets.update(widgets_collector.objects_collected)

        self._had_artists_on_last_run = len(graphics_collection.artists) > 0

        for artist in graphics_collection.artists:
            save_func_and_args_on_artists(artist, func=self.func, args=self.args)
            track_artist(artist)
        self.persist_self_on_artists(graphics_collection.artists)

        current_axeses_to_array_names_to_artists = get_axeses_to_array_names_to_artists(graphics_collection.artists)
        self._update_new_artists_from_previous_artists(previous_axeses_to_array_names_to_indices_and_artists,
                                                       current_axeses_to_array_names_to_artists)

        # We don't allow returning quibs as results from functions
        from pyquibbler.quib import Quib
        if isinstance(ret_val, Quib):
            ret_val = ret_val.get_value()

        return ret_val

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        """
        Create the new artists, then update them (if appropriate) with correct attributes (such as color) and place them
        in the same place they were in their axes.
        Return the function's result.
        """
        self._initialize_graphics_ndarr()
        # This implementation does not support partial calculation
        assert self._graphics_collection_ndarr.ndim == 0

        args, kwargs = proxify_args(self.args, self.kwargs) if self._pass_quibs \
            else self._prepare_args_for_call(valid_path)

        return self._run_single_call(self.func, self._graphics_collection_ndarr[()], args, kwargs)

    def redraw_if_appropriate(self):
        """
        Redraws the quib if it's appropriate
        """
        from .widgets import is_within_drag
        if self.update_type in [UpdateType.NEVER, UpdateType.CENTRAL] \
                or (self.update_type == UpdateType.DROP and is_within_drag()):
            return

        return self.get_value()
