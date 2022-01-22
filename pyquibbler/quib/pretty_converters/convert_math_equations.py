import enum
from pyquibbler.utilities.operators_with_reverse import REVERSE_OPERATOR_NAMES_TO_FUNCS
import operator
from dataclasses import dataclass
from typing import Callable, Tuple, Any
from abc import ABC, abstractmethod

import numpy as np


SPACE = ' '


class MathPrecedence(enum.IntEnum):
    VAR_NAME = 20
    PARENTHESIS = 19
    FUNCTION_CALL = 18
    SLICING = 17
    SUBSCRIPTION = 16
    ATTRIBUTE = 15
    EXPONENTIATION = 14
    BITWISE_NOT = 13
    POSNEG = 12
    MULDIV = 11
    ADDSUB = 10
    BITWISE_SHIFT = 9
    BITWISE_AND = 8
    BITWISE_XOR = 7
    BITWISE_OR = 6
    COMPARISON = 5
    BOOL_NOT = 4
    BOOL_AND = 3
    BOOL_OR = 2
    LAMBDA = 1
    VAR_NAME_WITH_SPACES = 0


@dataclass
class OperatorDefintion():
    symbol: str
    precedence: MathPrecedence
    commutative: bool = True

    def __str__(self):
        return self.symbol


class Operator(enum.Enum):
    POW = OperatorDefintion('**', MathPrecedence.EXPONENTIATION)
    NEG = OperatorDefintion('-', MathPrecedence.POSNEG)
    POS = OperatorDefintion('+', MathPrecedence.POSNEG)
    NOT = OperatorDefintion('~', MathPrecedence.POSNEG)
    MUL = OperatorDefintion('*', MathPrecedence.MULDIV)
    MATMUL = OperatorDefintion('@', MathPrecedence.MULDIV)
    TRUEDIV = OperatorDefintion('/', MathPrecedence.MULDIV, False)
    FLOORDIV = OperatorDefintion('//', MathPrecedence.MULDIV, False)
    MOD = OperatorDefintion('%', MathPrecedence.MULDIV, False)
    ADD = OperatorDefintion('+', MathPrecedence.ADDSUB)
    SUB = OperatorDefintion('-', MathPrecedence.ADDSUB, False)
    LSHIFT = OperatorDefintion('<<', MathPrecedence.BITWISE_SHIFT)
    RSHIFT = OperatorDefintion('>>', MathPrecedence.BITWISE_SHIFT)
    AND = OperatorDefintion('&', MathPrecedence.BITWISE_AND)
    XOR = OperatorDefintion('^', MathPrecedence.BITWISE_XOR)
    OR = OperatorDefintion('|', MathPrecedence.BITWISE_OR)
    LT = OperatorDefintion('<', MathPrecedence.COMPARISON)
    GT = OperatorDefintion('>', MathPrecedence.COMPARISON)
    LE = OperatorDefintion('<=', MathPrecedence.COMPARISON)
    GE = OperatorDefintion('>=', MathPrecedence.COMPARISON)
    EQ = OperatorDefintion('==', MathPrecedence.COMPARISON)
    NE = OperatorDefintion('!=', MathPrecedence.COMPARISON)


class MathExpression(ABC):
    @abstractmethod
    def __str__(self):
        pass

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


def add_parenthesis_if_needed(expr : MathExpression, needed : bool = False):
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

        return f"{left_side} {self.symbol} {right_side}"


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

    operator.truediv: Operator.TRUEDIV,
    np.divide: Operator.TRUEDIV,

    operator.floordiv: Operator.FLOORDIV,
    np.floor_divide: Operator.FLOORDIV,

    operator.mod: Operator.MOD,
    np.remainder: Operator.MOD,

    operator.sub: Operator.SUB,
    np.subtract: Operator.SUB,

    operator.pow: Operator.POW,
    np.power: Operator.POW
}

REVERSE_BINARY_FUNCS_TO_OPERATORS = {func: Operator[name.upper()[3:-2]] for
                                     name, func in REVERSE_OPERATOR_NAMES_TO_FUNCS.items()}


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
