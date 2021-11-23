import enum
import operator
from dataclasses import dataclass
from typing import List, Callable, Union

import numpy as np


class Operator(enum.Enum):
    LT = ('<', 0)
    GT = ('>', 0)
    LE = ('<=', 0)
    GE = ('>=', 0)
    EQ = ('==', 0)
    NE = ('!=', 0)
    ADD = ('+', 1)
    SUB = ('-', 1)
    MUL = ('*', 2)
    MATMUL = ('@', 2)
    DIV = ('/', 2)
    FLRDIV = ('//', 2)
    MOD = ('%', 2)
    NEG = ('-', 3)
    POS = ('+', 3)
    PWR = ('**', 4)


@dataclass
class MathExpression:
    operator: Operator
    left_side: Union['MathExpression', str, type(None)] = None
    right_side: Union['MathExpression', str, type(None)] = None

    @property
    def order(self):
        return self.operator.value[1]

    @property
    def symbol(self):
        return self.operator.value[0]

    def __eq__(self, other):
        return isinstance(self, MathExpression) and isinstance(other, MathExpression) \
               and self.operator == other.operator

    def __str__(self):
        left_side = self.left_side
        if isinstance(self.left_side, MathExpression) and (
                self.left_side.order < self.order
                # in equality operations, need parenthesis even when same order:
                # "(a < b) < c" is not "a < b < c"
                or (self.left_side.order == 0 and self.order == 0)
        ):
            left_side = f"({left_side})"

        right_side = self.right_side
        if isinstance(self.right_side, MathExpression) and (
                self.right_side.order < self.order
                # in equality operations, need parenthesis even when same order:
                # "a < (b < c)" is not "a < b < c"
                or (self.right_side.order == 0 and self.order == 0)
                # in subtract and divide order matters- this means the right side must be paranthesized if it's a
                # different symbol
                or (self.operator in {Operator.SUB, Operator.DIV, Operator.FLRDIV, Operator.MOD} and
                    self.right_side.order == self.order)
        ):
            right_side = f"({right_side})"

        if left_side and right_side:
            return f"{left_side} {self.symbol} {right_side}"
        elif right_side:
            return f"{self.symbol}{right_side}"
        elif left_side:
            return f"{left_side}{self.symbol}"
        else:
            assert False


def convert_binary_func_to_mathematical_notation(func: Callable,
                                                 args: List[Union[MathExpression, str]]) -> MathExpression:
    """
    Convert the binary func and pretty args to mathematical notation
    """
    operator = BINARY_FUNCS_TO_OPERATORS[func]
    return MathExpression(operator=operator, left_side=args[0], right_side=args[1])


def convert_unary_right_func_to_mathematical_notation(func: Callable,
                                                      args: List[Union[MathExpression, str]]) -> MathExpression:
    """
    Convert the unary func and pretty arg to mathematical notation
    """
    operator = UNARY_RIGHT_FUNCS_TO_OPERATORS[func]
    return MathExpression(operator=operator, right_side=args[0])


UNARY_RIGHT_FUNCS_TO_OPERATORS = {
    operator.pos: Operator.POS,
    np.positive: Operator.POS,

    operator.neg: Operator.NEG,
    np.negative: Operator.NEG,
}

BINARY_FUNCS_TO_OPERATORS = {
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

MATH_FUNCS_TO_CONVERTERS = {
    **{
        func: convert_binary_func_to_mathematical_notation
        for func, _ in BINARY_FUNCS_TO_OPERATORS.items()
    },
    **{
        func: convert_unary_right_func_to_mathematical_notation
        for func, _ in UNARY_RIGHT_FUNCS_TO_OPERATORS.items()
    },
}
