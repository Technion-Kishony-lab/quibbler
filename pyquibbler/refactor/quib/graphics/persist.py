from typing import Set, Callable, Iterable, Any

from matplotlib.artist import Artist

from pyquibbler.quib.graphics import CanvasEventHandler
from pyquibbler.refactor.quib.iterators import iter_object_type_in_args
from pyquibbler.refactor.quib.quib import Quib


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


def track_artist(artist: Artist):
    CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)


def persist_func_on_artists(quib, new_artists):
    for artist in new_artists:
        save_func_and_args_on_artists(artist, func=quib.func, args=quib.args)
        track_artist(artist)


def persist_quib_on_artists(quib: Quib, new_artists: Set[Artist]):
    """
    Persist self on all artists we're connected to, making sure we won't be garbage collected until they are
    off the screen
    We need to also go over args as there may be a situation in which the function did not create new artists, but
    did perform an action on an existing one, such as Axes.set_xlim
    """
    artists_to_persist_on = new_artists if new_artists else \
        iter_object_type_in_args(Artist, quib.args, quib.kwargs)
    for artist in artists_to_persist_on:
        quibs = getattr(artist, '_quibbler_graphics_function_quibs', set())
        quibs.add(quib)
        artist._quibbler_graphics_function_quibs = quibs


def persist_relevant_info_on_new_artists_for_quib(quib: Quib, new_artists):
    persist_quib_on_artists(quib, new_artists)
    persist_func_on_artists(quib, new_artists)
