from __future__ import annotations
import functools
import threading
from abc import ABC
from typing import List, Callable, Type
from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget


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
            if threading.get_ident() == self._thread_id:
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
