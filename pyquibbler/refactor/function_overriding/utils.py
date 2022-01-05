from typing import Callable

from pyquibbler.refactor.function_overriding.function_override import OverrideDefinition
from pyquibbler.refactor.function_definitions.exceptions import CannotFindDefinitionForFunctionException


def get_definition_for_function(func: Callable) -> OverrideDefinition:
    from pyquibbler.refactor.function_definitions.overriding import FUNCS_TO_DEFINITIONS
    try:
        if func not in FUNCS_TO_DEFINITIONS:
            raise CannotFindDefinitionForFunctionException(func)
        return FUNCS_TO_DEFINITIONS[func]
    except Exception:
        raise
