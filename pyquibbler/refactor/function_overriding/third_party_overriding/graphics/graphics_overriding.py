import functools
from dataclasses import dataclass

from typing import Dict, Any, Callable

from matplotlib.axes import Axes

from pyquibbler.refactor.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.refactor.function_definitions.function_definition import create_function_definition, FunctionDefinition
from pyquibbler.refactor.function_overriding.function_override import FunctionOverride
from pyquibbler.refactor.graphics import global_collecting
from pyquibbler.refactor.quib.function_running.function_runners.known_graphics.plot_runner import PlotRunner


@dataclass
class GraphicsOverride(FunctionOverride):

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return dict(
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


def axes_override(func_name, function_definition_kwargs=None):
    function_definition_kwargs = function_definition_kwargs or {}
    function_definition = create_function_definition(is_known_graphics_func=True, **function_definition_kwargs)
    return GraphicsOverride(func_name=func_name, module_or_cls=Axes, function_definition=function_definition)


def create_graphics_overrides():
    return [
        axes_override(func_name="plot", function_definition_kwargs=dict(function_runner_cls=PlotRunner)),
        *[
            axes_override(func_name=func_name) for func_name in [
                'imshow', 'text', 'bar', 'hist', 'pie', 'legend', '_sci', 'matshow', 'scatter'
            ]
        ],
        *[
            axes_override(func_name=func_name, function_definition_kwargs=dict(replace_previous_quibs_on_artists=True))
            for func_name in [
                'set_xlim', 'set_ylim', 'set_xticks', 'set_yticks', 'set_xlabel', 'set_ylabel',
                'set_title', 'set_visible', 'set_facecolor'
            ]
        ]

    ]


def override_graphics_functions_to_be_within_known_func_ctx():
    for override in create_graphics_overrides():
        setattr(override.module_or_cls, override.func_name,
                wrap_overridden_graphics_function(override.original_func))


