from dataclasses import dataclass
from typing import Callable, Tuple, Any, Mapping, Type, Dict

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import Path
from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


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


def backwards_translate(func_call: FuncCall,
                        path, shape=None, type_=None) -> Dict[Source, Path]:

    from pyquibbler.refactor.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func_call.func).backwards_path_translators
    # TODO: below should be in init of definition
    potential_translator_classes = potential_translator_classes or []
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException(NoTranslatorsFoundException)
    while True:
        # TODO: What if there's none left?
        cls: Type[BackwardsPathTranslator] = potential_translator_classes.pop()
        translator = cls(
            func_call=func_call,
            path=path,
            shape=shape,
            type_=type_
        )

        try:
            return translator.translate_in_order()
        except TodoExceptionFailedToTranslateExpected:
            pass


def forwards_translate(func_call: FuncCall,
                       sources_to_paths, shape=None, type_=None):
    # TODO test multiple scenarios with choosing inverters
    from pyquibbler.refactor.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func_call.func).forwards_path_translators
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException(func_call.func)
    while True:
        # TODO: What if there's none left?
        cls: Type[ForwardsPathTranslator] = potential_translator_classes.pop()
        translator = cls(
            func_call=func_call,
            shape=shape,
            type_=type_,
            sources_to_paths=sources_to_paths
        )

        try:
            return translator.translate()
        except TodoExceptionFailedToTranslateExpected:
            pass
