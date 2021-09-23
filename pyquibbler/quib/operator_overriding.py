"""
Override Quib operators by replacing magic methods with Quibs that represent the getattr of these magic methods
from the original values.
This could also be done by replacing the magic methods with Quib function wrappers
(see commit 6d06b9fe76e3b7279c1dd737152d9c3cc586ebec).
The first method has the advantage of being simple and easy to implement, but the disadvantage of create two quibs per
magic method call, and not being able to handle cases where a magic method is not present on a built-in type but the
operator works anyway (e.g. float.__ceil__).
"""
import magicmethods
from dis import opname
from inspect import currentframe
from operator import getitem

from .quib import Quib
from .function_quibs import DefaultFunctionQuib

## Reasons for skipping some magic method groups:
# typeconv:              python checks that the return value is of the expected type
# lifecycle, reflection: don't want to mess with that
# iassign, pickling:     not supported at the moment
# attributes:            overriding manually
# contextmanagers:       doesn't make sense to override
# descriptors:           Quibs shouldn't be used as descriptors
# copying:               already defined on the Quib class
# unary:                 not all builtin types implement them, so getattr fails (e.g. float.__ceil__)
# comparison, callables, representation, containers: change python's behavior unexpectedly
OVERRIDES = magicmethods.arithmetic + magicmethods.rarithmetic


def get_magic_method_wrapper(name: str):
    return DefaultFunctionQuib.create_wrapper(lambda val, *args, **kwargs: getattr(val, name)(*args, **kwargs))


def get_unpack_amount():
    # inspiration - https://stackoverflow.com/a/16481975/2907819
    frame = currentframe().f_back.f_back
    instruction_index = frame.f_lasti
    bytecode = frame.f_code.co_code
    instruction = bytecode[instruction_index]
    if opname[instruction] == 'UNPACK_SEQUENCE':
        return bytecode[instruction_index + 1]
    return None


def quib_getitem_override(self, item):
    unpack_amount = get_unpack_amount()
    if unpack_amount is not None:
        assert isinstance(item, int)
        if item >= unpack_amount:
            raise IndexError
    return DefaultFunctionQuib.create(getitem, (self, item))


def override_quib_operators():
    """
    Make operators (and other magic methods) on quibs return quibs.
    Overriding __getattr__ does not suffice because lookup of magic methods does not go
    through the standard getattr process.
    See more here: https://docs.python.org/3/reference/datamodel.html#special-method-lookup
    """
    Quib.__getitem__ = quib_getitem_override
    # Override a bunch of magic methods to enable operators to work.
    for magic_method_name in OVERRIDES:
        assert magic_method_name not in vars(Quib), magic_method_name
        setattr(Quib, magic_method_name, get_magic_method_wrapper(magic_method_name))
