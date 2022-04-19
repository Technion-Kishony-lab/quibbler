from __future__ import annotations
import functools
import threading
from abc import ABC, abstractmethod
from typing import List, Callable, Type
from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget
from matplotlib.pyplot import Axes

from pyquibbler.exceptions import PyQuibblerException


class UponCreation(ABC):

    cls: Type = NotImplemented

    def __init__(self, thread_id: int = None,
                 previous_init: Callable = None):
        self._thread_id = thread_id or threading.get_ident()
        self._previous_init = previous_init

    @abstractmethod
    def _on_creation(self, obj, *args, **kwargs):
        pass

    def wrap_object_creation(self, func):
        @functools.wraps(func)
        def wrapped_init(obj, *args, **kwargs):
            res = func(obj, *args, **kwargs)
            if threading.get_ident() == self._thread_id:
                self._on_creation(obj, *args, **kwargs)
            return res

        return wrapped_init

    def __enter__(self):
        self._previous_init = self.cls.__init__
        self.cls.__init__ = self.wrap_object_creation(self.cls.__init__)
        return self

    def __exit__(self, *_, **__):
        self.cls.__init__ = self._previous_init


class GraphicsCollector(UponCreation, ABC):
    """
    A context manager to begin global collecting of artists.
    After exiting the context manager use `get_artists_collected` to get a list of artists created during this time
    """

    cls: Type = NotImplemented

    def __init__(self, objects_collected: List = None, thread_id: int = None,
                 previous_init: Callable = None):
        self._objects_collected = objects_collected or []
        super(GraphicsCollector, self).__init__(thread_id=thread_id, previous_init=previous_init)

    @property
    def objects_collected(self):
        return self._objects_collected

    def _on_creation(self, obj, *args, **kwargs):
        self._objects_collected.append(obj)


class ArtistsCollector(GraphicsCollector):

    cls = Artist


class AxesWidgetsCollector(GraphicsCollector):

    cls = AxesWidget


class AxesCreatedDuringQuibEvaluationException(PyQuibblerException):

    def __str__(self):
        return f"Quibs are not allowed to create new axes.\n" \
               "Required axes should be created outside the quib function, before the quib is evaluated."


class AxesCreationPreventor(UponCreation):

    cls = Axes

    def _on_creation(self, obj, *args, **kwargs):
        raise AxesCreatedDuringQuibEvaluationException()
