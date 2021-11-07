import operator
from typing import List, Callable, Any

import numpy as np
from pyquibbler.quib import Quib


def convert_to_mathematical_notation(func: Callable, pretty_args: List[str]):
    """
    Convert the func and pretty args to mathematical notation
    """
    symbol = MATH_FUNCS_TO_SYMBOLS[func]
    return f" {symbol} ".join([p if ' ' not in p else f'({p})' for p in pretty_args])


MATH_FUNCS_TO_SYMBOLS = {
    operator.add: '+',
    np.add: '+',
    operator.mul: '*',
    np.multiply: '*',
    operator.truediv: '/',
    np.divide: '/',
    operator.sub: '-',
    np.subtract: '-',
    operator.pow: '^',
    np.power: '^'
}

MATH_FUNCS_TO_CONVERTERS = {
    **{
        func: convert_to_mathematical_notation
        for func, symbol in MATH_FUNCS_TO_SYMBOLS.items()
    }
}
