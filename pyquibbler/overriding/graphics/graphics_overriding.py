import functools
from dataclasses import dataclass

from typing import Dict, Any

from matplotlib.axes import Axes

from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.overriding.override_definition import OverrideDefinition


@dataclass
class GraphicsOverrideDefinition(OverrideDefinition):

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return dict(
            is_known_graphics_func=True,
            evaluate_now=GRAPHICS_EVALUATE_NOW
        )


AxesOverrideDefinition = functools.partial(GraphicsOverrideDefinition, module_or_cls=Axes)

GRAPHICS_DEFINITIONS = [
    AxesOverrideDefinition(
        func_name="plot"
    )
]
