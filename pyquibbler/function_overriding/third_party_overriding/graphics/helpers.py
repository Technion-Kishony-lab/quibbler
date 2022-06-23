import functools
from dataclasses import dataclass
from typing import Any

import matplotlib.widgets
from matplotlib.axes import Axes

from pyquibbler.env import PLOT_WITH_PICKER_TRUE_BY_DEFAULT
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.quib.graphics import artist_wrapper

from pyquibbler.quib.graphics.event_handling import CanvasEventHandler


@dataclass
class GraphicsOverride(FuncOverride):
    """
    An override of a function which is known to create graphics, and wants to be evaluated immediately as such
    """

    pass


@dataclass
class PlotOverride(GraphicsOverride):
    """
    An override of plt.plot
    """

    @staticmethod
    def _modify_kwargs(kwargs):
        if PLOT_WITH_PICKER_TRUE_BY_DEFAULT:
            if 'picker' not in kwargs:
                kwargs['picker'] = True
            elif kwargs['picker'] is False:
                kwargs['picker'] = 0  # `picker=False` does not really turn off picking


@dataclass
class AxesSetOverride(GraphicsOverride):

    @staticmethod
    def _call_wrapped_func(func, args, kwargs) -> Any:
        """
        An override of a axes setting functions with no quibs
        to remove any prior quib setters of same attribute.
        """

        result = func(*args, **kwargs)

        ax = args[0]
        name = func.__name__

        artist_wrapper.set_setter_quib(ax, name, None)

        return result


@dataclass
class AxesLimOverride(AxesSetOverride):

    @staticmethod
    def _call_wrapped_func(func, args, kwargs) -> Any:
        """
        An override of a set_xlim, set_ylim to allow tracking limit changes to axes.
        When mouse is pressed, changes to axis limits are reported to CanvasEventHandler for inverse assignment.
        Otherwise, the normal behavior of AxesSetOverrise is invoked.
        """
        from pyquibbler.graphics import is_pressed
        if is_pressed():
            result = func(*args, **kwargs)

            ax = args[0]
            CanvasEventHandler.get_or_create_initialized_event_handler(ax.figure.canvas). \
                handle_axes_limits_changed(ax, func, result)
            return result

        return AxesSetOverride._call_wrapped_func(func, args, kwargs)


graphics_override = functools.partial(override_with_cls, GraphicsOverride, is_graphics=True)
axes_override = functools.partial(graphics_override, Axes)

plot_override = functools.partial(override_with_cls, PlotOverride, Axes, is_graphics=True)

axes_setter_override = functools.partial(override_with_cls, AxesSetOverride, Axes, is_graphics=True,
                                         is_artist_setter=True)

widget_override = functools.partial(graphics_override, matplotlib.widgets)

axes_lim_override = functools.partial(override_with_cls, AxesLimOverride,
                                      Axes, is_graphics=True, is_artist_setter=True)
