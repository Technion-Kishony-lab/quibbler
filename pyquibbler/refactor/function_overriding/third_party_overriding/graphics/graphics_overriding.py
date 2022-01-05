import functools
from dataclasses import dataclass

from typing import Dict, Any, Callable

from matplotlib.axes import Axes

from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.function_overriding.function_override import FunctionOverride
from pyquibbler.refactor.graphics import global_collecting
from pyquibbler.refactor.quib.function_runners.known_graphics.plot_runner import PlotRunner


@dataclass
class GraphicsOverride(FunctionOverride):

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return dict(
            is_known_graphics_func=True,
            evaluate_now=GRAPHICS_EVALUATE_NOW
        )


def wrap_overridden_graphics_function(func: Callable) -> Callable:
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        # We need overridden funcs to be run in `overridden_graphics_function` context manager
        # so artists will be collected
        with global_collecting.overridden_graphics_function():
            return func(*args, **kwargs)

    return _wrapper


axes_override = functools.partial(GraphicsOverride, module_or_cls=Axes)


def create_graphics_overrides():
    return [
        axes_override(func_name="plot", function_definition=create_function_definition(function_runner_cls=PlotRunner)),
        axes_override(func_name="text")
    ]


def override_graphics_functions_to_be_within_known_func_ctx():
    for override in create_graphics_overrides():
        setattr(override.module_or_cls, override.func_name,
                wrap_overridden_graphics_function(override.original_func))


