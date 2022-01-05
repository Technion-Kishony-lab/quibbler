from typing import Callable

from pyquibbler.refactor.function_definitions.exceptions import CannotFindDefinitionForFunctionException
from pyquibbler.refactor.function_definitions.function_definition import FunctionDefinition

FUNCS_TO_DEFINITIONS = {}


def add_definition_for_function(func: Callable, function_definition: FunctionDefinition):
    """
    Add a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior)
    """
    FUNCS_TO_DEFINITIONS[func] = function_definition


def get_definition_for_function(func: Callable) -> FunctionDefinition:
    """
    Get a definition for the function
    """
    if func not in FUNCS_TO_DEFINITIONS:
        raise CannotFindDefinitionForFunctionException(func)
    return FUNCS_TO_DEFINITIONS[func]
