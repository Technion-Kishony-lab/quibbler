from typing import Callable

from pyquibbler.refactor.overriding.override_definition import OverrideDefinition
from pyquibbler.refactor.overriding.exceptions import CannotFindDefinitionForFunctionException


def get_definition_for_function(func: Callable) -> OverrideDefinition:
    from pyquibbler.refactor.overriding.overriding import FUNCS_TO_DEFINITIONS
    try:
        if func not in FUNCS_TO_DEFINITIONS:
            raise CannotFindDefinitionForFunctionException(func)
        return FUNCS_TO_DEFINITIONS[func]
    except Exception:
        print(1)
        raise
