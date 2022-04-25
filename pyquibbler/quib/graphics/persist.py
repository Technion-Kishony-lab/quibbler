from itertools import chain
from typing import Set, Callable, Iterable, Any

from matplotlib.artist import Artist

from pyquibbler.quib.graphics.event_handling import CanvasEventHandler
from pyquibbler.quib.utils.iterators import iter_object_type_in_args_kwargs
from pyquibbler.quib.quib import Quib


def track_artist(artist: Artist):
    CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)


def persist_func_on_artists(quib: Quib, new_artists):
    for artist in new_artists:
        track_artist(artist)


def persist_quib_on_artists(quib: Quib, new_artists: Set[Artist]):
    """
    Persist self on all artists we're connected to, making sure we won't be garbage collected until they are
    off the screen
    We need to also go over args as there may be a situation in which the function did not create new artists, but
    did perform an action on an existing one, such as Axes.set_xlim
    """

    artists_to_persist_on = new_artists \
        if new_artists else quib.handler.quib_function_call.get_objects_of_type_in_args_kwargs(Artist)
    for artist in artists_to_persist_on:
        artist._quibbler_artist_creating_quib = quib


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
    if quib.handler.func_definition.is_artist_setter:
        persist_func_on_artists(quib, artists)
        for artist in chain(artists, iter_object_type_in_args_kwargs(Artist, quib.args, quib.kwargs)):
            name = f'_quibbler_{quib.func.__name__}'
            current_quib = getattr(artist, name, None)
            if current_quib is not quib and current_quib is not None:
                for parent in current_quib.parents:
                    parent.handler.remove_child(current_quib)
            setattr(artist, name, quib)
    else:
        persist_relevant_info_on_new_artists_for_quib(quib, artists)
