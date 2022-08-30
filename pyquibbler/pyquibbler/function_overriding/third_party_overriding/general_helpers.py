import functools
from typing import List, Optional, Callable, Type, Tuple

from pyquibbler.function_definitions.types import RawArgument
from pyquibbler.function_definitions.func_definition import create_func_definition, FuncDefinition
from ..function_override import FuncOverride, ClassOverride, NotImplementedOverride


def override_with_cls(override_cls,
                      module_or_cls,
                      func_name: str,
                      data_source_arguments: List[RawArgument] = None,
                      forwards_path_translators: Optional[List] = None,
                      backwards_path_translators: Optional[List] = None,
                      inverters: Optional[List] = None,
                      quib_function_call_cls=None, is_file_loading=False, is_random=False,
                      pass_quibs: bool = False,
                      lazy: Optional[bool] = None,
                      is_artist_setter: bool = False,
                      is_graphics: bool = False,
                      func: Optional[Callable] = None,
                      should_remove_arguments_equal_to_defaults: bool = False,
                      func_definition_cls: Optional[Type[FuncDefinition]] = None,
                      allowed_kwarg_flags: Tuple[str] = (),
                      **kwargs):
    return override_cls(
        func_name=func_name,
        module_or_cls=module_or_cls,
        allowed_kwarg_flags=allowed_kwarg_flags,
        should_remove_arguments_equal_to_defaults=should_remove_arguments_equal_to_defaults,
        func_definition=create_func_definition(raw_data_source_arguments=data_source_arguments,
                                               is_random=is_random,
                                               is_file_loading=is_file_loading,
                                               is_graphics=is_graphics,
                                               pass_quibs=pass_quibs,
                                               lazy=lazy,
                                               is_artist_setter=is_artist_setter,
                                               inverters=inverters,
                                               backwards_path_translators=backwards_path_translators,
                                               forwards_path_translators=forwards_path_translators,
                                               quib_function_call_cls=quib_function_call_cls,
                                               func=func,
                                               func_definition_cls=func_definition_cls,
                                               **kwargs)
    )


def file_loading_override(module_or_cls, func_name: str):
    return FuncOverride(module_or_cls, func_name, FuncDefinition(is_file_loading=True))


override = functools.partial(override_with_cls, FuncOverride)


def override_class(module_or_cls, cls_to_override: str, **kwargs):
    return override_with_cls(ClassOverride,
                             getattr(module_or_cls, cls_to_override),
                             '__new__',
                             **kwargs)


def override_not_implemented(module_or_cls,
                             func_name: str,
                             message: str = ''):
    return NotImplementedOverride(module_or_cls=module_or_cls,
                                  func_name=func_name,
                                  message=message)
