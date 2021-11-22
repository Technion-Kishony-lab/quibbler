import enum
import operator
from dataclasses import dataclass
from typing import List, Callable, Union

import numpy as np


class Symbol(enum.Enum):
    LT = '<'
    GT = '>'
    LE = '<='
    GE = '>='
    EQ = '=='
    NE = '!='
    ADD = '+'
    SUB = '-'
    MUL = '*'
    MATMUL = '@'
    DIV = '/'
    FLRDIV = '//'
    MOD = '%'
    PWR = '^'


SYMBOLS_TO_ORDER = {
    Symbol.LT: 0,
    Symbol.GT: 0,
    Symbol.LE: 0,
    Symbol.GE: 0,
    Symbol.EQ: 0,
    Symbol.NE: 0,
    Symbol.ADD: 1,
    Symbol.SUB: 1,
    Symbol.MUL: 2,
    Symbol.MATMUL: 2,
    Symbol.DIV: 2,
    Symbol.FLRDIV: 2,
    Symbol.MOD: 2,
    Symbol.PWR: 3
}


@dataclass
class MathExpression:
    symbol: Symbol
    left_side: Union['MathExpression', str]
    right_side: Union['MathExpression', str]

    @property
    def order(self):
        return SYMBOLS_TO_ORDER[self.symbol]

    def __eq__(self, other):
        return isinstance(self, MathExpression) and isinstance(other, MathExpression) and self.symbol == other.symbol

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
                or (self.symbol in {Symbol.SUB, Symbol.DIV, Symbol.FLRDIV, Symbol.MOD} and
                    self.right_side.order == self.order)
        ):
            right_side = f"({right_side})"

        return f"{left_side} {self.symbol.value} {right_side}"


def convert_to_mathematical_notation(func: Callable, args: List[Union[MathExpression, str]]) -> MathExpression:
    """
    Convert the func and pretty args to mathematical notation
    """
    symbol = MATH_FUNCS_TO_SYMBOLS[func]
    return MathExpression(symbol=symbol, left_side=args[0], right_side=args[1])


MATH_FUNCS_TO_SYMBOLS = {
    operator.lt: Symbol.LT,
    np.less: Symbol.LT,

    operator.gt: Symbol.GT,
    np.greater: Symbol.GT,

    operator.le: Symbol.LE,
    np.less_equal: Symbol.LE,

    operator.ge: Symbol.GE,
    np.greater_equal: Symbol.GE,

    operator.eq: Symbol.EQ,
    np.equal: Symbol.EQ,

    operator.ne: Symbol.NE,
    np.not_equal: Symbol.NE,

    operator.add: Symbol.ADD,
    np.add: Symbol.ADD,

    operator.mul: Symbol.MUL,
    np.multiply: Symbol.MUL,

    operator.matmul: Symbol.MATMUL,
    np.matmul: Symbol.MATMUL,

    operator.truediv: Symbol.DIV,
    np.divide: Symbol.DIV,

    operator.floordiv: Symbol.FLRDIV,
    np.floor_divide: Symbol.FLRDIV,

    operator.mod: Symbol.MOD,
    np.remainder: Symbol.MOD,

    operator.sub: Symbol.SUB,
    np.subtract: Symbol.SUB,

    operator.pow: Symbol.PWR,
    np.power: Symbol.PWR
}

MATH_FUNCS_TO_CONVERTERS = {
    **{
        func: convert_to_mathematical_notation
        for func, symbol in MATH_FUNCS_TO_SYMBOLS.items()
    }
}
