from typing import Callable, Tuple, Any, Mapping, Type

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator


class NoTranslatorsFoundException(PyQuibblerException):
    pass


class TodoExceptionFailedToTranslateExpected(PyQuibblerException):
    pass


def backwards_translate(func_with_args_values: FuncWithArgsValues,
                        path, shape=None, type_=None):

    # TODO test multiple scenarios with choosing inverters
    from pyquibbler.refactor.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func_with_args_values.func).backwards_path_translators
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException()
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


def forwards_translate(func_with_args_values: FuncWithArgsValues,
                       sources_to_paths, shape=None, type_=None):
    # TODO test multiple scenarios with choosing inverters
    from pyquibbler.refactor.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func_with_args_values.func).forwards_path_translators
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException()
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
