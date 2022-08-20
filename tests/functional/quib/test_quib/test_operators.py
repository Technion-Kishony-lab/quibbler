import operator
from math import trunc, floor, ceil
import numpy as np

import pytest

from pyquibbler.env import LEN_RAISE_EXCEPTION, BOOL_RAISE_EXCEPTION
from pyquibbler.quib.quib import Quib

operator_names = {
    '__add__',
    '__sub__',
    '__mul__',
    '__truediv__',
    '__floordiv__',
    '__mod__',
    '__pow__',
    '__lshift__',
    '__and__',
    '__xor__',
    '__or__'
}


@pytest.mark.parametrize(['val1', 'val2'], [
    (1, 2),
    (1., 2.),
    (1., 2),
    (1, 2.)
])
@pytest.mark.parametrize('operator_name', operator_names)
def test_quib_forward_and_inverse_arithmetic_operators(create_quib_with_return_value, operator_name: str, val1, val2):
    op = getattr(operator, operator_name)
    quib1 = create_quib_with_return_value(val1)
    quib2 = create_quib_with_return_value(val2)

    if (isinstance(val1, float) or isinstance(val2, float)) and operator_name in {'__rshift__', '__lshift__', '__or__',
                                                                                  '__and__', '__xor__'}:
        # Bitwise operators don't work with floats
        result_quib = op(quib1, quib2)
        with pytest.raises(TypeError, match='.*'):
            result_quib.get_value()

    else:
        # Forward operators
        assert op(quib1, quib2).get_value() == op(val1, val2)
        assert op(quib1, val2).get_value() == op(val1, val2)
        # Reverse operators
        assert op(val1, quib2).get_value() == op(val1, val2)


@pytest.mark.parametrize('operator_name', operator_names)
def test_binary_operators_elementwise_invalidation(create_quib_with_return_value, operator_name: str):
    op = getattr(operator, operator_name)
    a = create_quib_with_return_value(np.array([0, 1, 2]), allow_overriding=True)
    b: Quib = op(a, 10).setp(cache_mode='on')
    b.get_value()

    # sanity:
    assert np.array_equal(b.handler.quib_function_call.cache._invalid_mask, [False, False, False])

    a[1] = 10
    assert np.array_equal(b.handler.quib_function_call.cache._invalid_mask, [False, True, False])


@pytest.mark.parametrize('val', [1, 1., -1, -1.])
@pytest.mark.parametrize('operator_name', ['__neg__', '__pos__', '__abs__', '__invert__'])
def test_quib_unary_operators(operator_name, val, create_quib_with_return_value):
    op = getattr(operator, operator_name)
    quib = create_quib_with_return_value(val)
    result_quib = op(quib)

    if isinstance(val, float) and operator_name in {'__invert__'}:
        # Bitwise operators don't work with floats
        with pytest.raises(TypeError, match='.*'):
            result_quib.get_value()
    else:
        assert result_quib.get_value() == op(val)


@pytest.mark.parametrize('val', [1, 1., -1, -1.])
@pytest.mark.parametrize('op', [round, trunc, floor, ceil])
def test_quib_rounding_operators(create_quib_with_return_value, op, val):
    quib = create_quib_with_return_value(val)
    result_quib = op(quib)

    result = result_quib.get_value()

    assert result == op(val)


@pytest.mark.regression
def test_quib_add_with_float_does_not_return_not_implemented(create_quib_with_return_value):
    function_quib = create_quib_with_return_value(1)
    add_function_quib = function_quib + 1.2

    value = add_function_quib.get_value()

    assert value == 2.2


def test_len_of_quib_not_allowed(create_quib_with_return_value):
    quib = create_quib_with_return_value([1, 2])
    with LEN_RAISE_EXCEPTION.temporary_set(True):
        with pytest.raises(TypeError, match='.*'):
            len(quib)


def test_len_of_quib_allowed(create_quib_with_return_value):
    quib = create_quib_with_return_value([1, 2])
    with LEN_RAISE_EXCEPTION.temporary_set(False):
        assert len(quib) == 2


def test_bool_of_quib_not_allowed(create_quib_with_return_value):
    quib = create_quib_with_return_value(1)
    with BOOL_RAISE_EXCEPTION.temporary_set(True):
        with pytest.raises(TypeError, match='.*'):
            bool(quib)


def test_bool_of_quib_allowed(create_quib_with_return_value):
    quib = create_quib_with_return_value(1)
    with BOOL_RAISE_EXCEPTION.temporary_set(False):
        assert bool(quib) == True


