from typing import Callable

from pyquibbler.refactor.function_definitions.exceptions import CannotFindDefinitionForFunctionException
from pyquibbler.refactor.function_definitions.function_definition import FunctionDefinition

FUNCS_TO_DEFINITIONS = {}


def add_definition_for_function(func: Callable, function_definition: FunctionDefinition):
    FUNCS_TO_DEFINITIONS[func] = function_definition


def get_definition_for_function(func: Callable) -> FunctionDefinition:
    if func not in FUNCS_TO_DEFINITIONS:
        raise CannotFindDefinitionForFunctionException(func)
    return FUNCS_TO_DEFINITIONS[func]
