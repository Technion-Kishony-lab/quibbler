from typing import Iterable, Optional

from pyquibbler.quib.graphics.artist_wrapper import QuibblerArtistWrapper
from pyquibbler.quib.graphics.event_handling import CanvasEventHandler

from weakref import ref
from pyquibbler.quib.quib import Quib
from pyquibbler.function_definitions import FuncArgsKwargs
from matplotlib.artist import Artist


def track_artist(artist):
    CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)


def persist_quib_on_created_artists(weak_ref_quib: ref[Quib], new_artists: Iterable[Artist], func_args_kwargs: FuncArgsKwargs):
    """
    Persist a graphic creating quib on the artists that it creates
    This method will be given as a callback to the function runner whenever it creates artists.
    """
    quib: Quib = weak_ref_quib()
    for artist in new_artists:
        QuibblerArtistWrapper(artist).set_creating_quib(quib)
        track_artist(artist)


def persist_quib_on_setted_artist(weak_ref_quib: ref[Quib], new_artists: Iterable[Artist], func_args_kwargs: FuncArgsKwargs):
    """
    Persist a graphic-setting quib on the artist whose properties it sets
    This method will be given as a callback to the function runner whenever it creates artists.
    """
    quib = weak_ref_quib()
    if func_args_kwargs.args and isinstance(func_args_kwargs.args[0], Artist):
        setted_artist = func_args_kwargs.args[0]
        setted_artist_wrapper = QuibblerArtistWrapper(setted_artist)
        track_artist(setted_artist)
        name = quib.func.__name__
        old_quib: Optional[Quib] = setted_artist_wrapper.get_setter_quib(name)
        if old_quib is not quib and old_quib is not None:
            old_quib.handler.disconnect_from_parents()
        setted_artist_wrapper.set_setter_quib(name, quib)
