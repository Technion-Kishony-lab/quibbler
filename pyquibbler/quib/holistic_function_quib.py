
from typing import Set, List, Callable, Tuple, Any, Mapping

from .function_quib import CacheBehavior
from pyquibbler.graphics import overriding, ArtistsRedrawer, GraphicsFunctionCall
from pyquibbler import graphics
from .default_function_quib import DefaultFunctionQuib, Quib
from pyquibbler.quib.utils import call_func_with_quib_values, iter_quibs_in_args


class HolisticFunctionQuib(DefaultFunctionQuib):
    """
    HolisticFunctionQuibs should be used when you want to run a function as a "singular unit" without creating
    quibs for every action you takes (any numpy function, any graphics function)

    This runs without creating any quibs for any graphics functions it runs- but on redraw, all artists it created
    will be removed and we will run the function again.
    It's important to note that on `get_value`, the quib will undo any graphics changes that were made, so as not to
    accidentally draw graphics twice
    """

    def __init__(self, artists_redrawers: Set,
                 children: List[Quib],
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: CacheBehavior,
                 graphics_calls: List[GraphicsFunctionCall],
                 corresponding_artist_redrawer: ArtistsRedrawer = None):

        super().__init__(artists_redrawers, children, func, args, kwargs, cache_behavior)
        self._graphics_calls = graphics_calls
        self._corresponding_artist_redrawer = corresponding_artist_redrawer

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, **kwargs):
        self = super(HolisticFunctionQuib, cls).create(func=func, func_args=func_args, func_kwargs=func_kwargs,
                                                       cache_behavior=cache_behavior, graphics_calls=[],
                                                       **kwargs)
        artists_redrawer = ArtistsRedrawer(func=self._redraw, args=tuple(), kwargs={}, artists=[])
        self._corresponding_artist_redrawer = artists_redrawer

        for quib in iter_quibs_in_args(func_args, func_kwargs):
            quib.add_artists_redrawer(artists_redrawer)

        return self

    def run_if_needed_and_draw(self):
        """
        Runs the function if needed and draws the graphics- this is in contrast to get_value where graphics will never
        be drawn
        """
        self._corresponding_artist_redrawer.redraw()

    def _redraw(self):
        # Makes sure our ._graphics_calls are updated to our current arg quibs
        self.get_value()

        artists = []
        for graphics_call in self._graphics_calls:
            artists.extend(graphics_call.run())

        return artists

    def _call_func(self):
        with graphics.global_graphics_collecting_mode():
            res = call_func_with_quib_values(self._func, self._args, self._kwargs)

        self._graphics_calls = graphics.get_graphics_calls_collected()

        artists_created = graphics.get_artists_collected()
        for artist in artists_created:
            artist.remove()

        return res
