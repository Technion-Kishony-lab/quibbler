from typing import Callable

from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.exceptions import CannotFindDefinitionForFunctionException


def get_definition_for_function(func: Callable) -> OverrideDefinition:
    from pyquibbler.overriding.overriding import NAMES_TO_DEFINITIONS
    if func.__name__ not in NAMES_TO_DEFINITIONS:
        raise CannotFindDefinitionForFunctionException(func)
    return NAMES_TO_DEFINITIONS[func.__name__]
