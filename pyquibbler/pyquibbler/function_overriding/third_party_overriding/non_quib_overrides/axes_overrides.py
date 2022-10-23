import functools
import itertools
from typing import Callable, Type

from pyquibbler.quib.quib import Quib
from pyquibbler.utilities.settable_cycle import SettableColorCycle
from pyquibbler.quib.graphics import artist_wrapper


def _get_wrapper_for_clear_axes(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, *args, **kwargs):
        artist_wrapper.clear_all_quibs(self)
        if hasattr(self, '_children'):
            for artist in self._children:
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


def _get_wrapper_for_funcs_that_can_work_on_quibs_returning_non_quibs(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, p):
        if isinstance(p, Quib):
            return func(self, p.get_value())
        else:
            return func(self, p)

    return _wrapper


def _get_wrapper_for_drag_pan(func: Callable):

    @functools.wraps(func)
    def _wrapper(self, button, key, x, y):
        # copied from original drag_pan, except adding `called_from_drag_pan=True`:
        points = self._get_pan_points(button, key, x, y)
        if points is not None:
            self.set_xlim(points[:, 0], called_from_drag_pan=True)
            self.set_ylim(points[:, 1], called_from_drag_pan=True)

    return _wrapper


def wrap_method(cls: Type, method_name: str, get_wrapper: Callable):
    func = getattr(cls, method_name)
    setattr(cls, method_name, get_wrapper(func))


def override_axes_methods():
    from matplotlib.axis import Axis
    wrap_method(Axis, 'clear', _get_wrapper_for_clear_axes)

    from matplotlib.axes._base import _AxesBase
    wrap_method(_AxesBase, 'cla', _get_wrapper_for_clear_axes)
    wrap_method(_AxesBase, 'drag_pan', _get_wrapper_for_drag_pan)

    for func in (
            'add_patch',
            '_sci'):
        wrap_method(_AxesBase, func, _get_wrapper_for_funcs_that_can_work_on_quibs_returning_non_quibs)

    from matplotlib.axes._base import _process_plot_var_args
    wrap_method(_process_plot_var_args, 'set_prop_cycle', _get_wrapper_for_set_prop_cycle)
