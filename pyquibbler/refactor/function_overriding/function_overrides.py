from typing import List

from pyquibbler.refactor.function_definitions.definitions import add_definition_for_function
from pyquibbler.refactor.function_overriding.function_override import FunctionOverride
from pyquibbler.refactor.function_overriding.third_party_overriding.graphics.graphics_overriding import create_graphics_overrides, \
    override_graphics_functions_to_be_within_known_func_ctx
from pyquibbler.refactor.function_overriding.third_party_overriding.graphics.widgets.switch_widgets_with_q_widgets import \
    switch_widgets_to_quib_supporting_widgets
from pyquibbler.refactor.function_overriding.third_party_overriding.graphics.widgets.widgets_overrides import \
    create_widget_overrides
from pyquibbler.refactor.function_overriding.inner.operator_overrides import get_operator_definitions
from pyquibbler.refactor.function_overriding.third_party_overriding.numpy.numpy_overrides import create_numpy_overrides
from pyquibbler.utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_new():
    """
    Override all relavent functions, both inner and third party, to support Quibs
    """

    function_overrides: List[FunctionOverride] = [*get_operator_definitions(),
                                                  *create_graphics_overrides(),
                                                  *create_numpy_overrides()]

    switch_widgets_to_quib_supporting_widgets()
    override_graphics_functions_to_be_within_known_func_ctx()
    for func_override in function_overrides:
        if func_override.function_definition:
            add_definition_for_function(func_override.original_func, func_override.function_definition)
        func_override.override()
