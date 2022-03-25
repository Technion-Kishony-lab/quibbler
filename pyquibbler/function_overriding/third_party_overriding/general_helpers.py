import functools
from typing import List, Optional, Callable, Type
from pyquibbler.function_definitions.types import RawArgument
from pyquibbler.function_definitions.func_definition import create_func_definition, FuncDefinition
from pyquibbler.function_overriding.function_override import FuncOverride


def override_with_cls(override_cls,
                      module_or_cls,
                      func_name: str,
                      data_source_arguments: List[RawArgument] = None,
                      forwards_path_translators: Optional[List] = None,
                      backwards_path_translators: Optional[List] = None,
                      inverters: Optional[List] = None,
                      quib_function_call_cls=None, is_file_loading_func=False, is_random_func=False,
                      call_func_with_quibs: bool = False,
                      evaluate_now: bool = None,
                      replace_previous_quibs_on_artists: bool = False,
                      is_graphics_func: bool = False,
                      func: Optional[Callable] = None,
                      func_definition_cls: Optional[Type[FuncDefinition]] = None,
                      **kwargs
                      ):
    return override_cls(
        func_name=func_name,
        module_or_cls=module_or_cls,
        function_definition=create_func_definition(raw_data_source_arguments=data_source_arguments,
                                                   is_random_func=is_random_func,
                                                   is_file_loading_func=is_file_loading_func,
                                                   is_graphics_func=is_graphics_func,
                                                   call_func_with_quibs=call_func_with_quibs,
                                                   evaluate_now=evaluate_now,
                                                   replace_previous_quibs_on_artists=replace_previous_quibs_on_artists,
                                                   inverters=inverters,
                                                   backwards_path_translators=backwards_path_translators,
                                                   forwards_path_translators=forwards_path_translators,
                                                   quib_function_call_cls=quib_function_call_cls, func=func,
                                                   func_definition_cls=func_definition_cls, **kwargs)
    )


def file_loading_override(module_or_cls, func_name: str):
    return FuncOverride(module_or_cls, func_name, FuncDefinition(is_file_loading_func=True))


override = functools.partial(override_with_cls, FuncOverride)
