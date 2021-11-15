import enum
import operator
from dataclasses import dataclass
from typing import List, Callable, Union

import numpy as np


class Symbol(enum.Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    EXP = '^'


SYMBOLS_TO_ORDER = {
    Symbol.ADD: 0,
    Symbol.SUB: 0,
    Symbol.MUL: 1,
    Symbol.DIV: 1,
    Symbol.EXP: 2
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
        if isinstance(self.left_side, MathExpression) and self.left_side.order < self.order:
            left_side = f"({left_side})"

        right_side = self.right_side
        if isinstance(self.right_side, MathExpression) and (
                self.right_side.order < self.order
                # in subtract and divide order matters- this means the right side must be paranthesized if it's a
                # different symbol
                or (
                    self.symbol == Symbol.SUB and self.right_side.order == self.order
                )
                or (
                    self.symbol == Symbol.DIV and self.right_side.order == self.order
                )
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
    operator.add: Symbol.ADD,
    np.add: Symbol.ADD,
    operator.mul: Symbol.MUL,
    np.multiply: Symbol.MUL,
    operator.truediv: Symbol.DIV,
    np.divide: Symbol.DIV,
    operator.sub: Symbol.SUB,
    np.subtract: Symbol.SUB,
    operator.pow: Symbol.EXP,
    np.power: Symbol.EXP
}

MATH_FUNCS_TO_CONVERTERS = {
    **{
        func: convert_to_mathematical_notation
        for func, symbol in MATH_FUNCS_TO_SYMBOLS.items()
    }
}
