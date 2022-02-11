import operator
from typing import Callable


def get_reversed_func(func: Callable):
    def _reversed(quib, obj):
        return func(obj, quib)
    _reversed.__name__ = f"{func.__name__}_reversed"
    _reversed.__qualname__ = f"{func.__name__}_reversed"
    return _reversed


BINARY_OPERATOR_NAMES = [
    '__add__',
    '__sub__',
    '__mul__',
    '__matmul__',
    '__truediv__',
    '__floordiv__',
    '__mod__',
    '__pow__',
    '__and__',
    '__xor__',
    '__or__',
    '__lshift__',
    '__rshift__',
]

REVERSE_OPERATOR_NAMES_TO_FUNCS = {}

for func_name in BINARY_OPERATOR_NAMES:
    reversed_func_name = '__r' + func_name[2:]
    func = getattr(operator, func_name)
    REVERSE_OPERATOR_NAMES_TO_FUNCS[reversed_func_name] = get_reversed_func(func)
