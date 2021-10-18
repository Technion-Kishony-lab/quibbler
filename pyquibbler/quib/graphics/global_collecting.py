from __future__ import annotations
import contextlib
import functools
import threading
from typing import List, Callable
from matplotlib.artist import Artist

from pyquibbler.exceptions import PyQuibblerException

ORIGINAL_ARTIST_INIT = Artist.__init__

CURRENT_THREAD_ID = None
GLOBAL_ARTIST_COLLECTORS = 0
OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING = 0


def is_within_artists_collector():
    """
    Returns whether there's an active artists collector at this moment
    """
    return GLOBAL_ARTIST_COLLECTORS > 0


class AlreadyCollectingArtistsException(PyQuibblerException):
    pass


class ArtistsCollector:
    """
    A context manager to begin global collecting of artists.
    After exiting the context manager use `get_artists_collected` to get a list of artists created during this time
    """

    def __init__(self, artists_collected: List[Artist] = None, thread_id: int = None,
                 raise_if_within_collector: bool = False, previous_init: Callable = None):
        self._artists_collected = artists_collected or []
        self._thread_id = thread_id or threading.get_ident()
        self._raise_if_within_collector = raise_if_within_collector
        self._previous_init = previous_init

    @property
    def artists_collected(self):
        return self._artists_collected

    def wrap_artist_creation(self, func):
        @functools.wraps(func)
        def wrapped_init(artist, *args, **kwargs):
            res = func(artist, *args, **kwargs)
            if threading.get_ident() == self._thread_id and OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING:
                self._artists_collected.append(artist)
            return res

        return wrapped_init

    def __enter__(self):
        global GLOBAL_ARTIST_COLLECTORS
        if self._raise_if_within_collector and GLOBAL_ARTIST_COLLECTORS:
            raise AlreadyCollectingArtistsException()
        GLOBAL_ARTIST_COLLECTORS += 1
        self._previous_init = Artist.__init__
        Artist.__init__ = self.wrap_artist_creation(Artist.__init__)
        return self

    def __exit__(self, *_, **__):
        global GLOBAL_ARTIST_COLLECTORS
        GLOBAL_ARTIST_COLLECTORS -= 1
        Artist.__init__ = self._previous_init


@contextlib.contextmanager
def overridden_graphics_function():
    """
    Any overridden graphics function should be run within this context manager.
    Even in global collecting mode, artists will NOT be collected if not within this context manager.
    This serves as an extra layer of protection to make sure we're only collecting artists from known functions.
    """
    global OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING
    OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING += 1
    yield
    OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING -= 1


class classproperty:
    def __init__(self, function: Callable):
        self.function = function

    def __get__(self, instance, owner):
        return self.function(owner)
