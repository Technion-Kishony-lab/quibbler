import functools
from dataclasses import dataclass, field
from typing import Dict, Any

import matplotlib.widgets
from matplotlib.axes import Axes

from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.quib.utils.miscellaneous import is_there_a_quib_in_args
from pyquibbler.env import EVALUATE_NOW

from pyquibbler.quib.graphics.event_handling import CanvasEventHandler


@dataclass
class GraphicsOverride(FuncOverride):
    """
    An override of a function which is known to create graphics, and wants to be evaluated immediately as such
    """

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return dict(
            evaluate_now=GRAPHICS_EVALUATE_NOW
        )


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
        name = f'_quibbler_{func.__name__}'
        if hasattr(ax, name):
            delattr(ax, name)
        return result


@dataclass
class AxesLimOverride(GraphicsOverride):
    """
    An override of a set_xlim, set_ylim to allow creating quibs as well as tracking limit changes to axes
    to be transfer to CanvasEventHandler for inverse assignment upon axes limits change.
    """

    def _create_quib_supporting_func(self):
        """
        Create a function which *can* support quibs (and return a quib as a result) if any argument is a quib
        If not, the function will simply run and return it's result, and the result is also sent to
        CanvasEventHandler.
        """

        wrapped_func = self.original_func

        @functools.wraps(wrapped_func)
        def _maybe_create_quib(*args, **kwargs):
            from pyquibbler.quib.factory import create_quib
            if is_there_a_quib_in_args(args, kwargs):
                flags = self._get_creation_flags(args, kwargs)
                evaluate_now = flags.pop('evaluate_now', EVALUATE_NOW)
                return create_quib(
                    func=wrapped_func,
                    args=args,
                    kwargs=kwargs,
                    evaluate_now=evaluate_now,
                    **flags
                )

            result = wrapped_func(*args, **kwargs)

            ax = args[0]
            CanvasEventHandler.get_or_create_initialized_event_handler(ax.figure.canvas). \
                handle_axes_changed(ax, wrapped_func, result)

            return result

        _maybe_create_quib.__quibbler_wrapped__ = wrapped_func
        _maybe_create_quib.__qualname__ = getattr(wrapped_func, '__name__', str(wrapped_func))

        return _maybe_create_quib


graphics_override = functools.partial(override_with_cls, GraphicsOverride, is_known_graphics_func=True)
axes_override = functools.partial(graphics_override, Axes)

replacing_axes_override = functools.partial(override_with_cls, AxesSetOverride, Axes, is_known_graphics_func=True,
                                            replace_previous_quibs_on_artists=True)

widget_override = functools.partial(graphics_override, matplotlib.widgets)

axes_lim_override = functools.partial(override_with_cls, AxesLimOverride,
                                      Axes, is_known_graphics_func=True, replace_previous_quibs_on_artists=True)
