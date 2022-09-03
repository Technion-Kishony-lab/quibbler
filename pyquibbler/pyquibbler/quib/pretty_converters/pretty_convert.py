import operator
import numpy as np

from typing import Callable, Tuple, Any, Dict

from .math_expressions.math_expression import MathExpression
from .math_expressions.get_item_expression import getitem_converter
from .math_expressions.func_call_expression import \
    is_str_format, str_format_call_converter, function_call_converter, vectorize_call_converter
from .math_expressions.operators_expressions import OPERATOR_FUNCS_TO_MATH_CONVERTERS


def get_math_expression_of_func_with_args_and_kwargs(func: Callable,
                                                     args: Tuple[Any, ...],
                                                     kwargs: Dict[str, Any]) -> MathExpression:
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
    if func is np.vectorize.__call__.__wrapped__:
        return vectorize_call_converter(func, args, kwargs)

    return function_call_converter(func, args, kwargs)
