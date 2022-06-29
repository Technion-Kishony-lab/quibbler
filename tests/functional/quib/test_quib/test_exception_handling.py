import pytest
from pyquibbler import q, iquib, initialize_quibbler
from pyquibbler.quib.external_call_failed_exception_handling import ExternalCallFailedException


@pytest.mark.show_quib_exceptions_as_quib_traceback(True)
def test_get_shape_raises_external_call_exception():
    a = iquib(1)
    b = a / 0  # division by 0
    c = b + 3
    try:
        c.get_shape()
    except ExternalCallFailedException as e:
        assert e.quibs_with_calls == [(b, 'get_blank_value()'), (c, 'get_shape()')]


@pytest.mark.show_quib_exceptions_as_quib_traceback(True)
def test_get_value_raises_external_call_exception():
    a = iquib(1)
    b = a / 0  # division by 0
    c = b + 3
    try:
        c.get_value()
    except ExternalCallFailedException as e:
        assert e.quibs_with_calls == [(b, 'get_blank_value()'), (c, 'get_value()')]


@pytest.mark.show_quib_exceptions_as_quib_traceback(True)
def test_get_shape_of_q_function_raises_external_call_exception():

    def divide_by_zero(x):
        return x / 0

    a = iquib(1)
    b = q(divide_by_zero, a)

    try:
        b.get_shape()
    except ExternalCallFailedException as e:
        assert e.quibs_with_calls == [(b, 'get_shape()')]


@pytest.mark.show_quib_exceptions_as_quib_traceback(True)
def test_exception_during_quib_creation():
    import numpy as np
    a = iquib(np.array([1,2]))
    b = np.swapaxes(a) # <--- missing positional argument
    try:
        b.get_shape()
    except ExternalCallFailedException as e:
        assert e.quibs_with_calls == [(b, 'get_shape()')]


@pytest.mark.show_quib_exceptions_as_quib_traceback(True)
def test_exception_in_overrider():
    # Incorrect assignments do not generate proper readable exceptions #207
    a = iquib(0)
    a[2] = 10
    try:
        a.get_value()
    except ExternalCallFailedException as e:
        assert e.quibs_with_calls == [(a, 'get_value()')]


@pytest.mark.show_quib_exceptions_as_quib_traceback(True)
def test_exception_in_overrider():
    # https://github.com/Technion-Kishony-lab/pyquibbler/issues/134
    a = q(list, range(4))
    a.allow_overriding = True
    a[2] = [20, 30]
    a[2][1] = 31
    a[2] = 7
    try:
        a.get_value()
    except ExternalCallFailedException as e:
        assert e.quibs_with_calls == [(a, 'get_value()')]


