import functools
from dataclasses import dataclass
from typing import Any

import matplotlib.widgets
import matplotlib.patches
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d import Axes3D

from pyquibbler.env import DRAGGABLE_PLOTS_BY_DEFAULT
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls, override_class
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
        if DRAGGABLE_PLOTS_BY_DEFAULT:
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
        if kwargs.pop('called_from_drag_pan', False):
            ax = args[0]
            lim = args[1]
            CanvasEventHandler.get_or_create_initialized_event_handler(ax.figure.canvas). \
                handle_axes_drag_pan(ax, func, lim)
        else:
            return AxesSetOverride._call_wrapped_func(func, args, kwargs)


graphics_override = functools.partial(override_with_cls, GraphicsOverride, is_graphics=True,
                                      should_remove_arguments_equal_to_defaults=True)

axes_override = functools.partial(graphics_override, Axes)

axes3d_override = functools.partial(graphics_override, Axes3D)

patches_override = functools.partial(override_class, matplotlib.patches, is_graphics=True)

plot_override = functools.partial(override_with_cls, PlotOverride, Axes, is_graphics=True,
                                  should_remove_arguments_equal_to_defaults=True, kwargs_to_ignore_in_repr={'picker'})

axes_setter_override = functools.partial(override_with_cls, AxesSetOverride, Axes, is_graphics=True,
                                         is_artist_setter=True,
                                         should_remove_arguments_equal_to_defaults=True)

widget_override = functools.partial(graphics_override, matplotlib.widgets)

axes_lim_override = functools.partial(override_with_cls, AxesLimOverride,
                                      Axes, is_graphics=True, is_artist_setter=True,
                                      should_remove_arguments_equal_to_defaults=True)
