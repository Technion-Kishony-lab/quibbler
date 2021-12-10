from dataclasses import dataclass
from typing import Callable

from pyquibbler.third_party_overriding.graphics.graphics_overriding import GRAPHICS_DEFINITIONS
from pyquibbler.third_party_overriding.graphics.widgets.switch_widgets_with_q_widgets import switch_widgets_to_quib_supporting_widgets
from .definitions import OverrideDefinition
from .graphics.widgets.widgets_overriding import WIDGET_DEFINITIONS
from .numpy_definitions import NUMPY_DEFINITIONS
from ..exceptions import PyQuibblerException
from ..utils import ensure_only_run_once_globally

ALL_DEFINITIONS = [*GRAPHICS_DEFINITIONS, *WIDGET_DEFINITIONS, *NUMPY_DEFINITIONS]
NAMES_TO_DEFINITIONS = {
    definition.func_name: definition
    for definition in ALL_DEFINITIONS
}


@dataclass
class CannotFindDefinitionForFunctionException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"There exists no overriding definition for `{self.func.__name__}`. Consider adding one!"


@ensure_only_run_once_globally
def override_third_party_funcs():
    switch_widgets_to_quib_supporting_widgets()
    for definition in ALL_DEFINITIONS:
        definition.override()


def get_definition_for_function(func: Callable) -> OverrideDefinition:
    if func.__name__ not in NAMES_TO_DEFINITIONS:
        raise CannotFindDefinitionForFunctionException(func)
    return NAMES_TO_DEFINITIONS[func.__name__]
