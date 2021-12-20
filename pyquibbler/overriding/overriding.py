import operator
from dataclasses import dataclass
from typing import Callable, List

from pyquibbler.overriding.graphics.graphics_overriding import GRAPHICS_DEFINITIONS
from pyquibbler.overriding.graphics.widgets.switch_widgets_with_q_widgets import switch_widgets_to_quib_supporting_widgets
from .override_definition import OverrideDefinition
from .graphics.widgets.widgets_overriding import WIDGET_DEFINITIONS
from .numpy_definitions import NUMPY_DEFINITIONS
from .operator_definitions import OPERATOR_DEFINITIONS
from .types import KeywordArgument, IndexArgument
from ..exceptions import PyQuibblerException
from ..utils import ensure_only_run_once_globally


THIRD_PARTY_DEFINITIONS = [*OPERATOR_DEFINITIONS, *GRAPHICS_DEFINITIONS, *WIDGET_DEFINITIONS, *NUMPY_DEFINITIONS]
ALL_DEFINITIONS: List[OverrideDefinition] = [*THIRD_PARTY_DEFINITIONS]
NAMES_TO_DEFINITIONS = {
    definition.func_name: definition
    for definition in ALL_DEFINITIONS
}

FUNCS_TO_DEFINITIONS = {
    definition.original_func: definition
    for definition in ALL_DEFINITIONS
}


@ensure_only_run_once_globally
def override_third_party_funcs():
    switch_widgets_to_quib_supporting_widgets()
    for definition in THIRD_PARTY_DEFINITIONS:
        definition.override()
