from __future__ import annotations

from typing import Callable, Union, Type, NamedTuple, Dict
from types import ModuleType

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


class FuncInfo(NamedTuple):
    func_definition: FuncDefinition
    module_or_cls: Union[ModuleType, Type]
    func_name: str
    is_overridden: bool


FUNCS_TO_FUNC_INFO: Dict[Callable, FuncInfo] = {}


def add_definition_for_function(func: Callable,
                                func_definition: FuncDefinition,
                                module_or_cls: Union[ModuleType, Type] = None,
                                func_name: str = None,
                                quib_creating_func: Callable = None,
                                ):
    """
    Add a definition for a function- this will allow quibbler to utilize Quibs with the function in a more
    specific manner (and not just use default behavior)
    """
    func_name = func_name if func_name else str(func)
    FUNCS_TO_FUNC_INFO[func] = FuncInfo(
        func_definition=func_definition,
        module_or_cls=module_or_cls,
        func_name=func_name,
        is_overridden=quib_creating_func is not None,
    )
    if quib_creating_func:
        quib_creating_func.func_definition = func_definition


def get_definition_for_function(func: Callable, return_default: bool = True) -> Union[FuncDefinition, None]:
    """
    Get a definition for the function
    """
    from pyquibbler.function_definitions.func_definition import FUNC_DEFINITION_DEFAULT, FuncDefinition
    if hasattr(func, 'func_definition') and isinstance(func.func_definition, FuncDefinition):
        return func.func_definition
    if func in FUNCS_TO_FUNC_INFO:
        return FUNCS_TO_FUNC_INFO[func].func_definition

    # Default function definition
    return FUNC_DEFINITION_DEFAULT if return_default else None
