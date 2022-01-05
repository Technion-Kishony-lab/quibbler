import operator
from math import trunc, floor, ceil

import pytest

from pyquibbler.refactor.function_overriding.inner.operator_overrides import get_arithmetic_definitions, get_unary_definitions


@pytest.mark.parametrize(['val1', 'val2'], [
    (1, 2),
    (1., 2.),
    (1., 2),
    (1, 2.)
])
@pytest.mark.parametrize('operator_name', {a.func_name for a in get_arithmetic_definitions()
                                           if not a.func_name.startswith('__r')} - {'__matmul__', '__divmod__'})
def test_quib_forward_and_inverse_arithmetic_operators(create_quib_with_return_value, operator_name: str, val1, val2):
    op = getattr(operator, operator_name)
    quib1 = create_quib_with_return_value(val1)
    quib2 = create_quib_with_return_value(val2)

    if (isinstance(val1, float) or isinstance(val2, float)) and operator_name in {'__rshift__', '__lshift__', '__or__',
                                                                                  '__and__', '__xor__'}:
        # Bitwise operators don't work with floats
        result_quib = op(quib1, quib2)
        with pytest.raises(TypeError):
            result_quib.get_value()

    else:
        # Forward operators
        assert op(quib1, quib2).get_value() == op(val1, val2)
        assert op(quib1, val2).get_value() == op(val1, val2)
        # Reverse operators
        assert op(val1, quib2).get_value() == op(val1, val2)


@pytest.mark.parametrize('val', [1, 1., -1, -1.])
@pytest.mark.parametrize('operator_name', [override.func_name for override in get_unary_definitions()])
def test_quib_unary_operators(operator_name, val, create_quib_with_return_value):
    op = getattr(operator, operator_name)
    quib = create_quib_with_return_value(val)
    result_quib = op(quib)

    if isinstance(val, float) and operator_name in {'__invert__'}:
        # Bitwise operators don't work with floats
        with pytest.raises(TypeError):
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

