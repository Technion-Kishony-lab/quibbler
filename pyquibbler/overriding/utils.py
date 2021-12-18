from typing import Callable

from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.exceptions import CannotFindDefinitionForFunctionException


def get_definition_for_function(func: Callable) -> OverrideDefinition:
    from pyquibbler.overriding.overriding import FUNCS_TO_DEFINITIONS
    # func = func if not hasattr(func, 'wrapped_func') else func.wrapped_func
    try:
        if func not in FUNCS_TO_DEFINITIONS:
            raise CannotFindDefinitionForFunctionException(func)
        return FUNCS_TO_DEFINITIONS[func]
    except Exception:
        print(1)
        raise
