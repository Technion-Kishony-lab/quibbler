from dataclasses import dataclass
from typing import Any, Callable
from abc import ABC

from pyquibbler.utilities.general_utils import Args
from ..math_precedence import MathPrecedence
from .math_expression import MathExpression
from .simple_expressions import object_to_math_expression, add_parenthesis_if_needed
from ..operators import Operator, BINARY_FUNCS_TO_OPERATORS, REVERSE_BINARY_FUNCS_TO_OPERATORS, \
    UNARY_RIGHT_FUNCS_TO_OPERATORS


@dataclass
class OperatorExpression(MathExpression, ABC):
    operator: Operator

    @property
    def precedence(self) -> int:
        return self.operator.value.precedence

    @property
    def symbol(self) -> str:
        return self.operator.value.symbol

    @property
    def commutative(self) -> bool:
        return self.operator.value.commutative

    def __eq__(self, other):
        return isinstance(other, OperatorExpression) and self.operator == other.operator


@dataclass
class BinaryOperatorExpression(OperatorExpression):
    left_side: Any = None
    right_side: Any = None

    def get_str(self, with_spaces: bool = True):

        left_side = object_to_math_expression(self.left_side)
        left_side = add_parenthesis_if_needed(left_side,
                                              left_side.precedence < self.precedence
                                              or left_side.precedence == MathPrecedence.COMPARISON
                                              and self.precedence == MathPrecedence.COMPARISON)
        right_side = object_to_math_expression(self.right_side)
        right_side = add_parenthesis_if_needed(right_side,
                                               right_side.precedence < self.precedence
                                               or (right_side.precedence == MathPrecedence.COMPARISON
                                                   and self.precedence == MathPrecedence.COMPARISON)
                                               or not self.commutative and right_side.precedence == self.precedence)

        add_spaces_left = left_side.precedence <= self.precedence and with_spaces
        add_spaces_right = right_side.precedence <= self.precedence and with_spaces
        add_space = with_spaces \
            or (left_side.precedence > self.precedence and isinstance(left_side, BinaryOperatorExpression)) \
            or (right_side.precedence > self.precedence and isinstance(right_side, BinaryOperatorExpression))

        space = ' ' if add_space else ''
        return f"{left_side.get_str(add_spaces_left)}" \
               f"{space}{self.symbol}{space}" \
               f"{right_side.get_str(add_spaces_right)}"


@dataclass
class LeftUnaryOperatorExpression(OperatorExpression):
    right_side: Any = None

    def get_str(self, with_spaces: bool = True):
        right_side = object_to_math_expression(self.right_side)
        right_side = add_parenthesis_if_needed(right_side,
                                               right_side.precedence < self.precedence
                                               or (right_side.precedence == MathPrecedence.COMPARISON
                                                   and self.precedence == MathPrecedence.COMPARISON)
                                               or not self.commutative and right_side.precedence == self.precedence)

        return f"{self.symbol}{right_side}"


def convert_binary_func_to_mathematical_expression(func: Callable, args: Args) -> MathExpression:
    """
    Convert the binary func and args to mathematical expression
    """
    operator = BINARY_FUNCS_TO_OPERATORS[func]
    return BinaryOperatorExpression(operator=operator, left_side=args[0], right_side=args[1])


def convert_reverse_binary_func_to_mathematical_expression(func: Callable, args: Args) -> MathExpression:
    """
    Convert the reverse binary func and args to mathematical expression
    """
    operator = REVERSE_BINARY_FUNCS_TO_OPERATORS[func]
    return BinaryOperatorExpression(operator=operator, left_side=args[1], right_side=args[0])


def convert_unary_right_func_to_mathematical_expression(func: Callable, args: Args) -> MathExpression:
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
