from __future__ import annotations
import contextlib
import functools
import threading
from abc import ABCMeta, ABC
from typing import List, Callable, Type
from matplotlib.artist import Artist
from matplotlib.widgets import Widget, AxesWidget

from pyquibbler.exceptions import PyQuibblerException

ORIGINAL_ARTIST_INIT = Artist.__init__

CURRENT_THREAD_ID = None
GLOBAL_ARTIST_COLLECTORS = 0
OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING = 0


class GraphicsCollector(ABC):
    """
    A context manager to begin global collecting of artists.
    After exiting the context manager use `get_artists_collected` to get a list of artists created during this time
    """

    cls: Type = NotImplemented

    def __init__(self, objects_collected: List = None, thread_id: int = None,
                 previous_init: Callable = None):
        self._objects_collected = objects_collected or []
        self._thread_id = thread_id or threading.get_ident()
        self._previous_init = previous_init

    @property
    def objects_collected(self):
        return self._objects_collected

    def wrap_object_creation(self, func):
        @functools.wraps(func)
        def wrapped_init(obj, *args, **kwargs):
            res = func(obj, *args, **kwargs)
            if threading.get_ident() == self._thread_id and OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING:
                self._objects_collected.append(obj)
            return res

        return wrapped_init

    def __enter__(self):
        self._previous_init = self.cls.__init__
        self.cls.__init__ = self.wrap_object_creation(self.cls.__init__)
        return self

    def __exit__(self, *_, **__):
        self.cls.__init__ = self._previous_init


class ArtistsCollector(GraphicsCollector):

    cls = Artist


class AxesWidgetsCollector(GraphicsCollector):

    cls = AxesWidget


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
