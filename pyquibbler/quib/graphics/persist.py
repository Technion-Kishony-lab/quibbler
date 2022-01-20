from itertools import chain
from typing import Set, Callable, Iterable, Any

from matplotlib.artist import Artist

from pyquibbler.quib.graphics.event_handling import CanvasEventHandler
from pyquibbler.quib.utils.iterators import iter_object_type_in_args
from pyquibbler.quib.quib import Quib


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

    artists_to_persist_on = new_artists if new_artists else quib._quib_function_call.get_objects_of_type_in_args_kwargs(Artist)
    for artist in artists_to_persist_on:
        quibs = getattr(artist, '_quibbler_graphics_function_quibs', set())
        quibs.add(quib)
        artist._quibbler_graphics_function_quibs = quibs


def persist_relevant_info_on_new_artists_for_quib(quib: Quib, new_artists):
    persist_quib_on_artists(quib, new_artists)
    persist_func_on_artists(quib, new_artists)


def persist_artists_on_quib_weak_ref(weak_ref_quib, artists):
    """
    This method will be given as a callback to the function runner whenever it creates artists.

    This can't be a method on the quib, because the callback has to be with a `weakref` so that we won't hold have a
    circular reference between the quib and the FuncRunner- The quib should hold the FuncRunner, and the
    functionrunner should have no knowledge of it
    """
    quib: Quib = weak_ref_quib()
    if quib._func_definition.replace_previous_quibs_on_artists:
        persist_func_on_artists(quib, artists)
        for artist in chain(artists, iter_object_type_in_args(Artist, quib.args, quib.kwargs)):
            name = f'_quibbler_{quib.func.__name__}'
            current_quib = getattr(artist, name, None)
            if current_quib is not quib and current_quib is not None:
                for parent in current_quib.parents:
                    parent.remove_child(current_quib)
            setattr(artist, name, quib)
    else:
        persist_relevant_info_on_new_artists_for_quib(quib, artists)
