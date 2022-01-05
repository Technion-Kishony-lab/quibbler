import functools
from dataclasses import dataclass

from typing import Dict, Any

from matplotlib.axes import Axes

from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.refactor.graphics.global_collecting import overridden_graphics_function
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition


@dataclass
class GraphicsOverrideDefinition(OverrideDefinition):

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return dict(
            is_known_graphics_func=True,
            evaluate_now=GRAPHICS_EVALUATE_NOW
        )

    def override(self):
        original_func = self.original_func

        @functools.wraps(original_func)
        def _run_within_known_graphics_ctx(*args, **kwargs):
            with overridden_graphics_function():
                return original_func(*args, **kwargs)

        setattr(self.module_or_cls, self.func_name, _run_within_known_graphics_ctx)
        return super(GraphicsOverrideDefinition, self).override()


axes_definition = functools.partial(GraphicsOverrideDefinition, module_or_cls=Axes)


def create_graphics_definitions():
    return [
        axes_definition(func_name="plot"),
        axes_definition(func_name="text")
    ]
