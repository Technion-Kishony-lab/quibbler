import functools
import itertools
from typing import Callable, Type

from pyquibbler import Quib
from pyquibbler.utilities.settable_cycle import SettableColorCycle
from pyquibbler.graphics.utils import TYPES_TO_ARTIST_ARRAY_NAMES
from pyquibbler.quib.graphics import artist_wrapper


def _get_wrapper_for_clear_axes(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, *args, **kwargs):
        artist_wrapper.clear_all_quibs(self)
        for array_name in TYPES_TO_ARTIST_ARRAY_NAMES.values():
            if hasattr(self, array_name):
                for artist in getattr(self, array_name):
                    artist_wrapper.clear_all_quibs(artist)
        return func(self, *args, **kwargs)

    return _wrapper


def _get_wrapper_for_set_prop_cycle(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, *args, **kwargs):
        itertools_cycle = itertools.cycle
        try:
            itertools.cycle = SettableColorCycle
            result = func(self, *args, **kwargs)
        finally:
            itertools.cycle = itertools_cycle
        return result

    return _wrapper


def _get_wrapper_for_add_patch(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, p):
        if isinstance(p, Quib):
            return func(self, p.get_value())
        else:
            return func(self, p)

    return _wrapper


def wrap_method(cls: Type, method_name: str, get_wrapper: Callable):
    func = getattr(cls, method_name)
    setattr(cls, method_name, get_wrapper(func))


def override_axes_methods():
    from matplotlib.axis import Axis
    wrap_method(Axis, 'clear', _get_wrapper_for_clear_axes)

    from matplotlib.axes._base import _AxesBase
    wrap_method(_AxesBase, 'cla', _get_wrapper_for_clear_axes)
    wrap_method(_AxesBase, 'add_patch', _get_wrapper_for_add_patch)

    from matplotlib.axes._base import _process_plot_var_args
    wrap_method(_process_plot_var_args, 'set_prop_cycle', _get_wrapper_for_set_prop_cycle)
