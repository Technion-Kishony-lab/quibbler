from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Union, Type
from types import ModuleType


if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition

FUNCS_TO_DEFINITIONS_MODULE_AND_NAME_ISOVERRIDDEN = {}


def add_definition_for_function(func: Callable,
                                function_definition: FuncDefinition,
                                module_or_cls: Union[ModuleType, Type] = None,
                                func_name: str = None,
                                is_overridden: bool = False,
                                ):
    """
    Add a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior)
    """
    func_name = func_name if func_name else str(func)
    FUNCS_TO_DEFINITIONS_MODULE_AND_NAME_ISOVERRIDDEN[func] = \
        (function_definition, module_or_cls, func_name, is_overridden)
    if function_definition:
        function_definition.func = func


def get_definition_for_function(func: Callable) -> FuncDefinition:
    """
    Get a definition for the function
    """
    from pyquibbler.function_definitions.func_definition import FuncDefinition
    if func not in FUNCS_TO_DEFINITIONS_MODULE_AND_NAME_ISOVERRIDDEN:
        # Default function definition
        return FuncDefinition()
    return FUNCS_TO_DEFINITIONS_MODULE_AND_NAME_ISOVERRIDDEN[func][0]
