import functools

import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.env import PRETTY_REPR


def test_qvectorize_pretty_repr():
    @np.vectorize
    def my_func():
        pass

    with PRETTY_REPR.temporary_set(True):
        assert repr(my_func) == "np.vectorize(my_func)"


@pytest.fixture
def signature():
    return '(w,h,c),(x)->(w2,h2,c)'


@pytest.fixture
def vectorized_func_with_signature(signature):
    @functools.partial(np.vectorize, signature=signature)
    def my_func():
        pass

    return my_func


def test_qvectorize_pretty_repr_with_signature(vectorized_func_with_signature, signature):
    with PRETTY_REPR.temporary_set(True):
        assert repr(vectorized_func_with_signature) == f"np.vectorize(my_func, {signature})"


@pytest.mark.get_variable_names(True)
def test_vectorize_pretty_repr(vectorized_func_with_signature, signature):
    a = iquib("pasten")
    b = iquib(np.array([42, 42, 42]))
    quib = vectorized_func_with_signature(a, b)

    with PRETTY_REPR.temporary_set(True):
        assert quib.pretty_repr() == f"quib = np.vectorize(my_func, {signature})(a, b)"

