import functools
from dataclasses import dataclass
from typing import List, Dict, Any

import matplotlib.widgets
from matplotlib.axes import Axes

from pyquibbler.env import GRAPHICS_EVALUATE_NOW
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override, override_with_cls
from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import RawArgument


@dataclass
class GraphicsOverride(FuncOverride):

    @property
    def _default_creation_flags(self) -> Dict[str, Any]:
        return dict(
            evaluate_now=GRAPHICS_EVALUATE_NOW
        )


graphics_override = functools.partial(override_with_cls, GraphicsOverride)
axes_override = functools.partial(graphics_override, Axes)
replacing_axes_override = functools.partial(axes_override, replace_previous_quibs_on_artists=True)
widget_override = functools.partial(graphics_override, matplotlib.widgets)

