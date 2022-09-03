import enum
import operator
from dataclasses import dataclass

import numpy as np

from pyquibbler.utilities.operators_with_reverse import REVERSE_OPERATOR_NAMES_TO_FUNCS
from .math_precedence import MathPrecedence


@dataclass
class OperatorDefinition:
    symbol: str
    precedence: MathPrecedence
    commutative: bool = True

    def __str__(self):
        return self.symbol


class Operator(enum.Enum):
    POW = OperatorDefinition('**', MathPrecedence.EXPONENTIATION)
    NEG = OperatorDefinition('-', MathPrecedence.POSNEG)
    POS = OperatorDefinition('+', MathPrecedence.POSNEG)
    NOT = OperatorDefinition('~', MathPrecedence.POSNEG)
    MUL = OperatorDefinition('*', MathPrecedence.MULDIV)
    MATMUL = OperatorDefinition('@', MathPrecedence.MULDIV)
    TRUEDIV = OperatorDefinition('/', MathPrecedence.MULDIV, False)
    FLOORDIV = OperatorDefinition('//', MathPrecedence.MULDIV, False)
    MOD = OperatorDefinition('%', MathPrecedence.MULDIV, False)
    ADD = OperatorDefinition('+', MathPrecedence.ADDSUB)
    SUB = OperatorDefinition('-', MathPrecedence.ADDSUB, False)
    LSHIFT = OperatorDefinition('<<', MathPrecedence.BITWISE_SHIFT)
    RSHIFT = OperatorDefinition('>>', MathPrecedence.BITWISE_SHIFT)
    AND = OperatorDefinition('&', MathPrecedence.BITWISE_AND)
    XOR = OperatorDefinition('^', MathPrecedence.BITWISE_XOR)
    OR = OperatorDefinition('|', MathPrecedence.BITWISE_OR)
    LT = OperatorDefinition('<', MathPrecedence.COMPARISON)
    GT = OperatorDefinition('>', MathPrecedence.COMPARISON)
    LE = OperatorDefinition('<=', MathPrecedence.COMPARISON)
    GE = OperatorDefinition('>=', MathPrecedence.COMPARISON)
    EQ = OperatorDefinition('==', MathPrecedence.COMPARISON)
    NE = OperatorDefinition('!=', MathPrecedence.COMPARISON)


UNARY_RIGHT_FUNCS_TO_OPERATORS = {
    operator.pos: Operator.POS,
    np.positive: Operator.POS,

    operator.neg: Operator.NEG,
    np.negative: Operator.NEG,

    operator.not_: Operator.NOT,
    np.logical_not: Operator.NOT,

    operator.invert: Operator.NOT,
    np.invert: Operator.NOT,
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
