from dataclasses import dataclass
from typing import Callable, Tuple, Any, Mapping, Type

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator


@dataclass
class NoTranslatorsFoundException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"No translator was found for {self.func}"


class TodoExceptionFailedToTranslateExpected(PyQuibblerException):
    pass


def split_path(path):
    components_at_end = path[1:]
    current_components = path[0:1]
    if len(path) > 0 and path[0].references_field_in_field_array():
        components_at_end = [path[0], *components_at_end]
        current_components = []
    return current_components, components_at_end


def backwards_translate(func_with_args_values: FuncCall,
                        path, shape=None, type_=None):

    from pyquibbler.refactor.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func_with_args_values.func).backwards_path_translators
    # TODO: below should be in init of definition
    potential_translator_classes = potential_translator_classes or []
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException(NoTranslatorsFoundException)
    while True:
        # TODO: What if there's none left?
        cls: Type[BackwardsPathTranslator] = potential_translator_classes.pop()
        translator = cls(
            func_with_args_values=func_with_args_values,
            path=path,
            shape=shape,
            type_=type_
        )

        try:
            return translator.translate_in_order()
        except TodoExceptionFailedToTranslateExpected:
            pass


def forwards_translate(func_with_args_values: FuncCall,
                       sources_to_paths, shape=None, type_=None):
    # TODO test multiple scenarios with choosing inverters
    from pyquibbler.refactor.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func_with_args_values.func).forwards_path_translators
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException(func_with_args_values.func)
    while True:
        # TODO: What if there's none left?
        cls: Type[ForwardsPathTranslator] = potential_translator_classes.pop()
        translator = cls(
            func_with_args_values=func_with_args_values,
            shape=shape,
            type_=type_,
            sources_to_paths=sources_to_paths
        )

        try:
            return translator.translate()
        except TodoExceptionFailedToTranslateExpected:
            pass
