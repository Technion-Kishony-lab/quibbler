import operator
from math import trunc, floor, ceil
from typing import Callable, Tuple

from .quib import Quib
from .default_function_quib import DefaultFunctionQuib


def operator_override(operator_name: str) -> Tuple[str, Callable]:
    return operator_name, getattr(operator, operator_name)


def reverse_operator_override(operator_name: str) -> Tuple[str, Callable]:
    non_reverse_operator = getattr(operator, '__' + operator_name[3:])
    return operator_name, lambda self, other: non_reverse_operator(other, self)


QUIB_OVERRIDES = [
    (Quib, [
        ###### Emulating numeric types
        # Binary operators
        operator_override('__add__'),
        operator_override('__sub__'),
        operator_override('__mul__'),
        operator_override('__matmul__'),
        operator_override('__truediv__'),
        operator_override('__floordiv__'),
        operator_override('__mod__'),
        ('__divmod__', divmod),
        operator_override('__pow__'),
        operator_override('__lshift__'),
        operator_override('__rshift__'),
        operator_override('__and__'),
        operator_override('__xor__'),
        operator_override('__or__'),
        # Reverse binary operators
        reverse_operator_override('__radd__'),
        reverse_operator_override('__rsub__'),
        reverse_operator_override('__rmul__'),
        reverse_operator_override('__rmatmul__'),
        reverse_operator_override('__rtruediv__'),
        reverse_operator_override('__rfloordiv__'),
        reverse_operator_override('__rmod__'),
        ('__rdivmod__', lambda self, other, modulo=None: divmod(other, self, modulo)),
        reverse_operator_override('__rpow__'),
        reverse_operator_override('__rlshift__'),
        reverse_operator_override('__rrshift__'),
        reverse_operator_override('__rand__'),
        reverse_operator_override('__rxor__'),
        reverse_operator_override('__ror__'),
        # Unary operators
        operator_override('__neg__'),
        operator_override('__pos__'),
        operator_override('__abs__'),
        operator_override('__invert__'),
        # Conversions
        ('__complex__', complex),
        ('__int__', int),
        ('__float__', float),
        # Index
        operator_override('__index__'),
        # Rounding
        ('__round__', round),
        ('__trunc__', trunc),
        ('__floor__', floor),
        ('__ceil__', ceil),

        ('__getattr__', getattr),
        ('__call__', lambda func, *args, **kwargs: func(*args, **kwargs)),
        # '__lt__',
        # '__le__',
        # '__eq__',
        # '__ne__',
        # '__ge__',
        # '__gt__',
        # '__not__',
        # '__inv__',
        # '__concat__',
        # '__contains__',
        operator_override('__getitem__'),
    ]),
]


def override_quib_operators():
    for quib_cls, overrides in QUIB_OVERRIDES:
        for name, wrapped in overrides:
            setattr(quib_cls, name, DefaultFunctionQuib.create_wrapper(wrapped))
# ['abs', 'add', 'and_', 'attrgetter', 'concat', 'contains', 'countOf',
#            'delitem', 'eq', 'floordiv', 'ge', 'getitem', 'gt', 'iadd', 'iand',
#            'iconcat', 'ifloordiv', 'ilshift', 'imatmul', 'imod', 'imul',
#            'index', 'indexOf', 'inv', 'invert', 'ior', 'ipow', 'irshift',
#            'is_', 'is_not', 'isub', 'itemgetter', 'itruediv', 'ixor', 'le',
#            'length_hint', 'lshift', 'lt', 'matmul', 'methodcaller', 'mod',
#            'mul', 'ne', 'neg', 'not_', 'or_', 'pos', 'pow', 'rshift',
#            'setitem', 'sub', 'truediv', 'truth', 'xor']
