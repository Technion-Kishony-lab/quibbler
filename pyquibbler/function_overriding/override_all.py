from typing import List

from pyquibbler.function_definitions.definitions import add_definition_for_function
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.non_quib_overrides import switch_widgets_to_quib_supporting_widgets, \
    override_graphics_functions_to_be_within_known_func_ctx
from pyquibbler.function_overriding.quib_overrides.operators.overrides import create_operator_overrides
from pyquibbler.function_overriding.quib_overrides.quib_methods import create_quib_method_overrides
from pyquibbler.function_overriding.third_party_overriding.numpy.overrides import create_numpy_overrides
from pyquibbler.function_overriding.third_party_overriding.graphics.overrides import create_graphics_overrides
from pyquibbler.utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_all():
    """
    Override all relavent functions, both operators and third party, to support Quibs
    """

    function_overrides: List[FuncOverride] = [*create_operator_overrides(),
                                              *create_graphics_overrides(),
                                              *create_numpy_overrides(),
                                              *create_quib_method_overrides()]

    switch_widgets_to_quib_supporting_widgets()
    override_graphics_functions_to_be_within_known_func_ctx()
    for func_override in function_overrides:
        if func_override.function_definition:
            add_definition_for_function(func_override.original_func, func_override.function_definition)
        func_override.override()
