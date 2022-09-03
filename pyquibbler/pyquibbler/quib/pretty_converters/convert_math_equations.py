from typing import Callable, Tuple, Any

from .math_expression import MathExpression, BinaryOperatorExpression, LeftUnaryOperatorExpression
from .operators import BINARY_FUNCS_TO_OPERATORS, REVERSE_BINARY_FUNCS_TO_OPERATORS, UNARY_RIGHT_FUNCS_TO_OPERATORS


def convert_binary_func_to_mathematical_expression(func: Callable,
                                                   args: Tuple[Any, ...]) -> MathExpression:
    """
    Convert the binary func and args to mathematical expression
    """
    operator = BINARY_FUNCS_TO_OPERATORS[func]
    return BinaryOperatorExpression(operator=operator, left_side=args[0], right_side=args[1])


def convert_reverse_binary_func_to_mathematical_expression(func: Callable,
                                                           args: Tuple[Any, ...]) -> MathExpression:
    """
    Convert the reverse binary func and args to mathematical expression
    """
    operator = REVERSE_BINARY_FUNCS_TO_OPERATORS[func]
    return BinaryOperatorExpression(operator=operator, left_side=args[1], right_side=args[0])


def convert_unary_right_func_to_mathematical_expression(func: Callable,
                                                        args: Tuple[Any, ...]) -> MathExpression:
    """
    Convert the unary func and pretty arg to mathematical expression
    """
    operator = UNARY_RIGHT_FUNCS_TO_OPERATORS[func]
    return LeftUnaryOperatorExpression(operator=operator, right_side=args[0])


OPERATOR_FUNCS_TO_MATH_CONVERTERS = {
    **{
        func: convert_binary_func_to_mathematical_expression
        for func in BINARY_FUNCS_TO_OPERATORS.keys()
    },
    **{
        func: convert_reverse_binary_func_to_mathematical_expression
        for func in REVERSE_BINARY_FUNCS_TO_OPERATORS.keys()
    },
    **{
        func: convert_unary_right_func_to_mathematical_expression
        for func in UNARY_RIGHT_FUNCS_TO_OPERATORS.keys()
    },
}
