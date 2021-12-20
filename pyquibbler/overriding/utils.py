from typing import Callable

from pyquibbler.overriding.override_definition import OverrideDefinition
from pyquibbler.overriding.exceptions import CannotFindDefinitionForFunctionException


def get_original_func_from_partialled_func(func: Callable):
    return func if not hasattr(func, 'wrapped_func_of_partial') else func.wrapped_func_of_partial


def get_definition_for_function(func: Callable) -> OverrideDefinition:
    from pyquibbler.overriding.overriding import FUNCS_TO_DEFINITIONS
    func = get_original_func_from_partialled_func(func)
    try:
        if func not in FUNCS_TO_DEFINITIONS:
            raise CannotFindDefinitionForFunctionException(func)
        return FUNCS_TO_DEFINITIONS[func]
    except Exception:
        print(1)
        raise
