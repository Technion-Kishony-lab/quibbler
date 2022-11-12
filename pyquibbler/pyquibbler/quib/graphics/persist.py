from __future__ import annotations

from dataclasses import dataclass

from typing import Iterable
from abc import ABC, abstractmethod
from weakref import ReferenceType
from matplotlib.artist import Artist

from pyquibbler.quib.graphics.event_handling import CanvasEventHandler
from pyquibbler.function_definitions import FuncArgsKwargs
from . import artist_wrapper

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


def track_artist(artist):
    if artist.figure:
        CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)


@dataclass
class RunFunctionWithQuibArg(ABC):
    weak_ref_quib: ReferenceType[Quib]

    @property
    def quib(self):
        return self.weak_ref_quib()

    def __call__(self, *args, **kwargs):
        return self.called_function(self.quib, *args, **kwargs)

    @staticmethod
    @abstractmethod
    def called_function(quib: Quib, *args, **kwargs):
        pass


class PersistQuibOnCreatedArtists(RunFunctionWithQuibArg):

    @staticmethod
    def called_function(quib: Quib, new_artists: Iterable[Artist], func_args_kwargs: FuncArgsKwargs):
        """
        Persist a graphic creating quib on the artists that it creates
        This method will be given as a callback to the function runner whenever it creates artists.
        """
        for artist in new_artists:
            if artist_wrapper.get_creating_quib(artist) is None:
                artist_wrapper.set_creating_quib(artist, quib)
                track_artist(artist)
            else:
                artist_wrapper.get_upstream_caller_quibs(artist).add(quib)


class PersistQuibOnSettedArtist(RunFunctionWithQuibArg):

    @staticmethod
    def called_function(quib: Quib, new_artists: Iterable[Artist], func_args_kwargs: FuncArgsKwargs):
        """
        Persist a graphic-setting quib on the artist whose properties it sets
        This method will be given as a callback to the function runner whenever it creates artists.
        """
        if func_args_kwargs.args and isinstance(func_args_kwargs.args[0], Artist):
            setted_artist = func_args_kwargs.args[0]
            track_artist(setted_artist)
            name = quib.func.__name__
            old_quib = artist_wrapper.get_setter_quib(setted_artist, name)
            if old_quib is not quib and old_quib is not None:
                old_quib.handler.disconnect_from_parents()
            artist_wrapper.set_setter_quib(setted_artist, name, quib)
