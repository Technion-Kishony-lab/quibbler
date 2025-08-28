import operator
import numpy as np

from typing import Callable, Any

from pyquibbler.utilities.general_utils import Args, Kwargs

from .math_expressions.call_method_expression import CallMethodExpression
from .math_expressions.getattr_expression import getattr_converter
from .math_expressions.math_expression import MathExpression
from .math_expressions.getitem_expression import getitem_converter
from .math_expressions.func_call_expression import \
    is_str_format, str_format_call_converter, function_call_converter, vectorize_call_converter
from .math_expressions.operators_expressions import OPERATOR_FUNCS_TO_MATH_CONVERTERS
from pyquibbler.utilities.iterators import is_user_object


def is_bound_method(obj: Any, func: Callable) -> bool:
    return hasattr(obj, func.__name__)


def is_method_call(func: Callable, args: Args, kwargs: Kwargs) -> bool:
    if len(args) == 0:
        return False
    obj = args[0]
    return is_user_object(obj) and is_bound_method(obj, func)


def get_math_expression_of_func_with_args_and_kwargs(func: Callable,
                                                     args: Args,
                                                     kwargs: Kwargs) -> MathExpression:
    """
    Get the pretty value of a function, using a special converter if possible,
    defaulting to a standard func(xxx) if not.
    """

    if not kwargs and func in OPERATOR_FUNCS_TO_MATH_CONVERTERS:
        return OPERATOR_FUNCS_TO_MATH_CONVERTERS[func](func, args)

    if is_str_format(func):
        return str_format_call_converter(func, args, kwargs)

    if not kwargs and func is operator.getitem:
        return getitem_converter(func, args)

    if not kwargs and func is getattr:
        return getattr_converter(func, args)

    if func is np.vectorize.__call__.__wrapped__:
        return vectorize_call_converter(func, args, kwargs)

    from ..specialized_functions.quiby_methods import CallObjectMethod
    if isinstance(func, CallObjectMethod):
        return CallMethodExpression(func.method, args, kwargs)

    if is_method_call(func, args, kwargs):
        return CallMethodExpression(func.__name__, args, kwargs)

    return function_call_converter(func, args, kwargs)
