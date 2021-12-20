from typing import List

from pyquibbler.refactor.overriding.graphics.graphics_overriding import create_graphics_definitions
from pyquibbler.refactor.overriding.graphics.widgets.switch_widgets_with_q_widgets import switch_widgets_to_quib_supporting_widgets
from .override_definition import OverrideDefinition
from .graphics.widgets.widgets_overriding import create_widget_definitions
from .numpy_definitions import create_numpy_definitions
from .operator_definitions import get_operator_definitions
from pyquibbler.utils import ensure_only_run_once_globally


NAMES_TO_DEFINITIONS = {}

FUNCS_TO_DEFINITIONS = {}


@ensure_only_run_once_globally
def override_third_party_funcs():
    global FUNCS_TO_DEFINITIONS, NAMES_TO_DEFINITIONS
    definitions = [*get_operator_definitions(),
                               *create_graphics_definitions(),
                               *create_widget_definitions(),
                               *create_numpy_definitions()]

    FUNCS_TO_DEFINITIONS = {
        definition.original_func: definition
        for definition in definitions
    }
    NAMES_TO_DEFINITIONS = {
        definition.func_name: definition
        for definition in definitions
    }

    switch_widgets_to_quib_supporting_widgets()
    for definition in definitions:
        definition.override()
