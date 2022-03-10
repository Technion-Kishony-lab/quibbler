from pyquibbler import q, iquib, override_all
from pyquibbler.quib.external_call_failed_exception_handling import ExternalCallFailedException


def test_get_shape_raises_external_call_exception():
    a = iquib(1)
    b = a / 0  # division by 0
    c = b + 3
    try:
        c.get_shape()
    except Exception as e:
        assert isinstance(e, ExternalCallFailedException)


def test_get_value_raises_external_call_exception():
    a = iquib(1)
    b = a / 0  # division by 0
    c = b + 3
    try:
        print(c.get_value())
    except Exception as e:
        assert isinstance(e, ExternalCallFailedException)


def test_get_shape_of_q_function_raises_external_call_exception():

    def divide_by_zero(x):
        return x / 0

    a = iquib(1)
    b = q(divide_by_zero, a)

    try:
        b.get_shape()
    except Exception as e:
        assert isinstance(e, ExternalCallFailedException)
