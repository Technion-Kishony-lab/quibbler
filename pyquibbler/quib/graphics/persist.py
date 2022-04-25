import weakref
from typing import Iterable, Optional

from matplotlib.artist import Artist

from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.quib.graphics.event_handling import CanvasEventHandler
from pyquibbler.quib.quib import Quib


def track_artist(artist: Artist):
    CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)


def persist_quib_on_created_artists(weak_ref_quib: weakref.ref[Quib], new_artists: Iterable[Artist], func_args_kwargs: FuncArgsKwargs):
    """
    Persist a graphic creating quib on the artists that it creates
    This method will be given as a callback to the function runner whenever it creates artists.
    """
    quib: Quib = weak_ref_quib()
    for artist in new_artists:
        artist._quibbler_artist_creating_quib = quib
        track_artist(artist)


def persist_quib_on_setted_artist(weak_ref_quib: weakref.ref[Quib], new_artists: Iterable[Artist], func_args_kwargs: FuncArgsKwargs):
    """
    Persist a graphic-setting quib on the artist whose properties it sets
    This method will be given as a callback to the function runner whenever it creates artists.
    """
    quib = weak_ref_quib()
    if func_args_kwargs.args and isinstance(func_args_kwargs.args[0], Artist):
        setted_artist = func_args_kwargs.args[0]
        track_artist(setted_artist)
        name = f'_quibbler_{quib.func.__name__}'
        current_quib: Optional[Quib] = getattr(setted_artist, name, None)
        if current_quib is not quib and current_quib is not None:
            current_quib.handler.disconnect_from_parents()
        setattr(setted_artist, name, quib)
