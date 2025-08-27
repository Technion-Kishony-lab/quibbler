from __future__ import annotations
import functools
import threading

from abc import ABC, abstractmethod
from typing import List, Type, Dict, Optional

from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.widgets import AxesWidget
from matplotlib.pyplot import Axes

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.graphics.process_plot_var_args import quibbler_process_plot_var_args


def get_current_axes_if_exists() -> Optional[Axes]:
    """
    Get the current axes if any exist, without creating new figures or axes.
    """
    try:
        fig_nums = plt.get_fignums()
        if not fig_nums:
            return None
    except (TypeError, AttributeError):
        # Handle cases where figure numbers can't be sorted (e.g., Mock objects in tests)
        return None

    try:
        from matplotlib import _pylab_helpers
        if not _pylab_helpers.Gcf.figs:
            return None

        current_fig_manager = _pylab_helpers.Gcf.get_active()
        if current_fig_manager is None:
            return None

        fig = current_fig_manager.canvas.figure
        if not fig.axes:
            return None

        return fig._axstack.current()
    except (TypeError, AttributeError, KeyError):
        # Handle any other Mock-related or matplotlib internal errors
        return None


class UponMethodCall(ABC):
    cls: Type = NotImplemented
    method_name: str = None

    def __init__(self, thread_id: int = None):
        self._thread_id = thread_id or threading.get_ident()
        self._original_method = None

    @abstractmethod
    def _on_method_call(self, obj, *args, **kwargs):
        pass

    def wrap_object_method(self, func):
        @functools.wraps(func)
        def wrapped_method(obj, *args, **kwargs):
            if threading.get_ident() == self._thread_id:
                self._on_method_call(obj, *args, **kwargs)
            res = func(obj, *args, **kwargs)
            return res

        return wrapped_method

    def __enter__(self):
        func = getattr(self.cls, self.method_name)
        self._original_method = func
        setattr(self.cls, self.method_name, self.wrap_object_method(func))
        return self

    def __exit__(self, *_, **__):
        setattr(self.cls, self.method_name, self._original_method)


class UponCreation(UponMethodCall, ABC):
    method_name = '__init__'


class GraphicsCollector(UponCreation, ABC):
    """
    A context manager to begin global collecting of artists.
    After exiting the context manager use `get_artists_collected` to get a list of artists created during this time
    """

    cls: Type = NotImplemented

    def __init__(self, objects_collected: List = None, thread_id: int = None):
        self._objects_collected = objects_collected or []
        super(GraphicsCollector, self).__init__(thread_id=thread_id)

    @property
    def objects_collected(self):
        return self._objects_collected

    def _on_method_call(self, obj, *args, **kwargs):
        if not isinstance(obj, (Figure, Axes)):
            self._objects_collected.append(obj)


class ArtistsCollector(GraphicsCollector):
    cls = Artist


class AxesWidgetsCollector(GraphicsCollector):
    cls = AxesWidget


class AxesCreatedDuringQuibEvaluationException(PyQuibblerException):

    def __str__(self):
        return "Quibs are not allowed to create new axes.\n" \
               "Required axes should be created outside the quib function, before the quib is evaluated."


class AxesCreationPreventor(UponCreation):
    cls = Axes

    def _on_method_call(self, obj, *args, **kwargs):
        raise AxesCreatedDuringQuibEvaluationException()


class ColorCyclerIndexCollector:

    def __init__(self):
        self._color_cyclers_to_index: Dict[quibbler_process_plot_var_args, int] = dict()

    @property
    def color_cyclers_to_index(self):
        return self._color_cyclers_to_index

    def __enter__(self):
        quibbler_process_plot_var_args.callback = self._on_next_index
        return self

    def __exit__(self, *_, **__):
        quibbler_process_plot_var_args.callback = None

    def _on_next_index(self, obj: quibbler_process_plot_var_args, index):
        if obj not in self._color_cyclers_to_index:
            self._color_cyclers_to_index[obj] = index


class AxesManager:

    def __init__(self, original_focal_axes: Optional[Axes] = None):
        self.original_focal_axes: Optional[Axes] = original_focal_axes

    def __enter__(self):
        if self.original_focal_axes is not None:
            plt.sca(self.original_focal_axes)
        else:
            # we want to get the current axes if there is any, but not create one if there isn't:
            self.original_focal_axes = get_current_axes_if_exists()
        return self

    def __exit__(self, *_, **__):
        pass
