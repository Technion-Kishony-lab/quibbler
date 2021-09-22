import magicmethods

from .quib import Quib
from .default_function_quib import DefaultFunctionQuib

# skipping:
# No need:             lifecycle, iassign, attributes, reflection, contextmanagers, descriptors, copying, pickling
# Unexpected behavior: comparison, callables, representation, containers
OVERRIDES = set(magicmethods.unary + magicmethods.arithmetic + magicmethods.rarithmetic +
                magicmethods.typeconv + ['__getitem__'])


class MagicDescriptor(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        return DefaultFunctionQuib.create(getattr, (instance, self.name))


def override_quib_operators():
    Quib.__getattr__ = DefaultFunctionQuib.create_wrapper(getattr)
    Quib.__call__ = DefaultFunctionQuib.create_wrapper(lambda func, *args, **kwargs: func(*args, **kwargs))
    for magic_method_name in OVERRIDES:
        assert magic_method_name not in vars(Quib), magic_method_name
        setattr(Quib, magic_method_name, MagicDescriptor(magic_method_name))
