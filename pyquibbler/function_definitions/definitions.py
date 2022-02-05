from __future__ import annotations
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition

FUNCS_TO_DEFINITIONS = {}


def add_definition_for_function(func: Callable, function_definition: FuncDefinition):
    """
    Add a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior)
    """
    FUNCS_TO_DEFINITIONS[func] = function_definition
    function_definition.func = func


def get_definition_for_function(func: Callable) -> FuncDefinition:
    """
    Get a definition for the function
    """
    from pyquibbler.function_definitions.func_definition import FuncDefinition
    func = getattr(func, '__quibbler_third_party_called__', func)
    if func not in FUNCS_TO_DEFINITIONS:
        # Default function definition
        return FuncDefinition()
    return FUNCS_TO_DEFINITIONS[func]
