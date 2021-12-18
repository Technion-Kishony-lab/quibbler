from typing import Callable, Tuple, Any, Mapping, Type

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.translators import BACKWARDS_TRANSLATORS


class NoTranslatorsFoundException(PyQuibblerException):
    pass


class TodoExceptionFailedToTranslateExpected(PyQuibblerException):
    pass


def backwards_translate(func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any],
                        path, shape=None, type_=None):

    # TODO test multiple scenarios with choosing inverters
    from pyquibbler.overriding import get_definition_for_function
    potential_translator_classes = get_definition_for_function(func).backwards_path_translators
    potential_translator_classes = list(sorted(potential_translator_classes, key=lambda c: c.PRIORITY))
    if len(potential_translator_classes) == 0:
        raise NoTranslatorsFoundException()
    while True:
        # TODO: What if there's none left?
        cls: Type[BackwardsPathTranslator] = potential_translator_classes.pop()
        translator = cls(
            func_with_args_values=FuncWithArgsValues.from_function_call(
                func=func,
                args=args,
                kwargs=kwargs,
                include_defaults=True
            ),
            path=path,
            shape=shape,
            type_=type_
        )

        try:
            return translator.translate()
        except TodoExceptionFailedToTranslateExpected:
            pass
