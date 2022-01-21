import enum
import operator
from dataclasses import dataclass
from typing import Callable, Tuple, Any
from abc import ABC, abstractmethod

import numpy as np


@dataclass
class OperatorDefintion():
    symbol: str
    precedence: int
    commutative: bool = True

    def __str__(self):
        return self.symbol


class Operator(enum.Enum):
    LT = OperatorDefintion('<', 0)
    GT = OperatorDefintion('>', 0)
    LE = OperatorDefintion('<=', 0)
    GE = OperatorDefintion('>=', 0)
    EQ = OperatorDefintion('==', 0)
    NE = OperatorDefintion('!=', 0)
    OR = OperatorDefintion('|', 1)
    XOR = OperatorDefintion('^', 1)
    AND = OperatorDefintion('&', 2)
    NOT = OperatorDefintion('~', 3)
    ADD = OperatorDefintion('+', 4)
    SUB = OperatorDefintion('-', 4, False)
    MUL = OperatorDefintion('*', 5)
    MATMUL = OperatorDefintion('@', 5)
    DIV = OperatorDefintion('/', 5, False)
    FLRDIV = OperatorDefintion('//', 5, False)
    MOD = OperatorDefintion('%', 5, False)
    NEG = OperatorDefintion('-', 6)
    POS = OperatorDefintion('+', 6)
    PWR = OperatorDefintion('**', 7)


TOP_PRECEDENCE = 100


class MathExpression(ABC):
    @abstractmethod
    def __str__(self):
        pass

    @property
    @abstractmethod
    def precedence(self) -> int:
        pass

    def get_str(self, add_parentheses : bool = False):
        return '(' + str(self) + ')' if add_parentheses \
            else str(self)


class TopPrecedenceMathExpression(MathExpression, ABC):

    @property
    def precedence(self) -> int:
        return TOP_PRECEDENCE


@dataclass
class StringMathExpression(TopPrecedenceMathExpression):
    label: str

    def __str__(self):
        return self.label


class FailedMathExpression(StringMathExpression):
    def __init__(self):
        self.label = "[exception during repr]"


@dataclass
class ValueMathExpression(TopPrecedenceMathExpression):
    value: Any

    def __str__(self):
        return repr(self.value)


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
        left_side = object_to_math_expression(self.left_side)
        left_side = left_side.get_str(left_side.precedence < self.precedence or
                                      left_side.precedence == 0 and self.precedence == 0)
        right_side = object_to_math_expression(self.right_side)
        right_side = right_side.get_str(
                right_side.precedence < self.precedence
                or (right_side.precedence == 0 and self.precedence == 0)
                or not self.commutative and right_side.precedence == self.precedence)

        return f"{left_side} {self.symbol} {right_side}"


@dataclass
class UnaryOperatorExpression(OperatorExpression):
    right_side: Any = None

    def __str__(self):
        right_side = object_to_math_expression(self.right_side)
        right_side = right_side.get_str(
                right_side.precedence < self.precedence
                or (right_side.precedence == 0 and self.precedence == 0)
                or not self.commutative and right_side.precedence == self.precedence)

        return f"{self.symbol}{right_side}"


def convert_binary_func_to_mathematical_expression(func: Callable,
                                                   args: Tuple[Any, ...]) -> MathExpression:
    """
    Convert the binary func and pretty args to mathematical notation
    """
    operator = BINARY_FUNCS_TO_OPERATORS[func]
    return BinaryOperatorExpression(operator=operator, left_side=args[0], right_side=args[1])


def convert_unary_right_func_to_mathematical_expression(func: Callable,
                                                        args: Tuple[Any, ...]) -> MathExpression:
    """
    Convert the unary func and pretty arg to mathematical notation
    """
    operator = UNARY_RIGHT_FUNCS_TO_OPERATORS[func]
    return UnaryOperatorExpression(operator=operator, right_side=args[0])


UNARY_RIGHT_FUNCS_TO_OPERATORS = {
    operator.pos: Operator.POS,
    np.positive: Operator.POS,

    operator.neg: Operator.NEG,
    np.negative: Operator.NEG,

    operator.not_: Operator.NOT,
    np.logical_not: Operator.NOT,
}

BINARY_FUNCS_TO_OPERATORS = {
    operator.and_: Operator.AND,
    np.logical_and: Operator.AND,

    operator.or_: Operator.OR,
    np.logical_or: Operator.OR,

    operator.xor: Operator.XOR,
    np.logical_xor: Operator.XOR,

    operator.lt: Operator.LT,
    np.less: Operator.LT,

    operator.gt: Operator.GT,
    np.greater: Operator.GT,

    operator.le: Operator.LE,
    np.less_equal: Operator.LE,

    operator.ge: Operator.GE,
    np.greater_equal: Operator.GE,

    operator.eq: Operator.EQ,
    np.equal: Operator.EQ,

    operator.ne: Operator.NE,
    np.not_equal: Operator.NE,

    operator.add: Operator.ADD,
    np.add: Operator.ADD,

    operator.mul: Operator.MUL,
    np.multiply: Operator.MUL,

    operator.matmul: Operator.MATMUL,
    np.matmul: Operator.MATMUL,

    operator.truediv: Operator.DIV,
    np.divide: Operator.DIV,

    operator.floordiv: Operator.FLRDIV,
    np.floor_divide: Operator.FLRDIV,

    operator.mod: Operator.MOD,
    np.remainder: Operator.MOD,

    operator.sub: Operator.SUB,
    np.subtract: Operator.SUB,

    operator.pow: Operator.PWR,
    np.power: Operator.PWR
}

OPERATOR_FUNCS_TO_MATH_CONVERTERS = {
    **{
        func: convert_binary_func_to_mathematical_expression
        for func in BINARY_FUNCS_TO_OPERATORS.keys()
    },
    **{
        func: convert_unary_right_func_to_mathematical_expression
        for func in UNARY_RIGHT_FUNCS_TO_OPERATORS.keys()
    },
}
