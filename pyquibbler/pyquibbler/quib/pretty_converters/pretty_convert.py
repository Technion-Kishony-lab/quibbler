import operator
import numpy as np

from typing import Callable, Tuple, Any, Mapping

from pyquibbler.env import REPR_RETURNS_SHORT_NAME
from .get_item import getitem_converter
from .math_expression import MathExpression, FunctionCallMathExpression
from .convert_math_equations import OPERATOR_FUNCS_TO_MATH_CONVERTERS


def vectorize_call_converter(func: Callable, args: Tuple[Any, ...]) -> FunctionCallMathExpression:
    func_being_called, *args = args
    return FunctionCallMathExpression(str(func_being_called), args, {})


def function_call_converter(func: Callable,
                            args: Tuple[Any, ...],
                            kwargs: Mapping[str, Any]) -> FunctionCallMathExpression:
    func_name = getattr(func, '__name__', str(func))
    return FunctionCallMathExpression(func_name, args, kwargs)


def str_format_call_converter(func: Callable,
                              args: Tuple[Any, ...],
                              kwargs: Mapping[str, Any]) -> FunctionCallMathExpression:
    func_name = getattr(func, '__name__', str(func))
    str_ = getattr(func, '__reduce__')()[1][0]
    str_format_name = f'"{str_}".{func_name}'
    return FunctionCallMathExpression(str_format_name, args, kwargs)


def is_str_format(func: Callable) -> bool:
    return getattr(func, '__qualname__', None) == 'str.format'


def get_pretty_value_of_func_with_args_and_kwargs(func: Callable,
                                                  args: Tuple[Any, ...],
                                                  kwargs: Mapping[str, Any]) -> MathExpression:
    """
    Get the pretty value of a function, using a special converter if possible (eg for math notation) and defaulting
    to a standard func(xxx) if not
    """

    with REPR_RETURNS_SHORT_NAME.temporary_set(True):
        # For now, no ability to special convert if kwargs exist
        if not kwargs and func in CONVERTERS:
            pretty_value = CONVERTERS[func](func, args)
        elif is_str_format(func):
            pretty_value = str_format_call_converter(func, args, kwargs)
        else:
            pretty_value = function_call_converter(func, args, kwargs)

        return pretty_value


CONVERTERS = {
    **OPERATOR_FUNCS_TO_MATH_CONVERTERS,
    operator.getitem: getitem_converter,
    np.vectorize.__call__: vectorize_call_converter
}
