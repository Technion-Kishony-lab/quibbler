from dataclasses import dataclass
from typing import Any
from abc import ABC, abstractmethod

from .operators import Operator
from .math_precedence import MathPrecedence

SPACE = ' '


class MathExpression(ABC):
    @abstractmethod
    def __str__(self):
        pass

    def get_str(self, with_spaces: bool = True):
        return self.__str__()

    def get_math_expression(self):
        return self

    @property
    @abstractmethod
    def precedence(self) -> MathPrecedence:
        pass


@dataclass
class StringMathExpression(MathExpression):
    label: str
    label_precedence: MathPrecedence = None

    def __str__(self):
        return self.label

    @property
    def precedence(self) -> MathPrecedence:
        return self.label_precedence


class NameMathExpression(StringMathExpression):
    @property
    def precedence(self) -> int:
        return MathPrecedence.VAR_NAME_WITH_SPACES if SPACE in self.label \
            else MathPrecedence.VAR_NAME


class FailedMathExpression(StringMathExpression):
    def __init__(self):
        self.label = "[exception during repr]"
        self.label_precedence = MathPrecedence.PARENTHESIS


def add_parenthesis_if_needed(expr: MathExpression, needed: bool = False) -> MathExpression:
    return StringMathExpression(f'({expr})', MathPrecedence.PARENTHESIS) if needed else expr


@dataclass
class ValueMathExpression(MathExpression):
    value: Any

    def __str__(self):
        return repr(self.value)

    @property
    def precedence(self) -> MathPrecedence:
        return MathPrecedence.VAR_NAME


def object_to_math_expression(obj: Any):
    return obj.get_math_expression() if hasattr(obj, 'get_math_expression') \
            else ValueMathExpression(obj)


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

    def __str__(self):
        return self.get_str()

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

    def __str__(self):
        right_side = object_to_math_expression(self.right_side)
        right_side = add_parenthesis_if_needed(right_side,
                                               right_side.precedence < self.precedence
                                               or (right_side.precedence == MathPrecedence.COMPARISON
                                                   and self.precedence == MathPrecedence.COMPARISON)
                                               or not self.commutative and right_side.precedence == self.precedence)

        return f"{self.symbol}{right_side}"
