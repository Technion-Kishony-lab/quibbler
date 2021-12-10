

# TODO: Move as part of operators
import operator

import pytest

from pyquibbler.overriding.operator_definitions import ARITHMETIC_OPERATORS_DEFINITIONS


@pytest.mark.parametrize(['val1', 'val2'], [
    (1, 2),
    (1., 2.),
    (1., 2),
    (1, 2.)
])
@pytest.mark.parametrize('operator_name', {a.func_name for a in ARITHMETIC_OPERATORS_DEFINITIONS} - {'__matmul__', '__divmod__'})
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
