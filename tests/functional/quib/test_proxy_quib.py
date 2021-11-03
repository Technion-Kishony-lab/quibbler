import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.quib.proxy_quib import ProxyQuib


@pytest.fixture
def wrapped_quib():
    return iquib(np.array([0]))


@pytest.fixture
def proxy_quib(wrapped_quib):
    return ProxyQuib(wrapped_quib)


def test_proxy_quib_returns_value_of_wrapped_quib(proxy_quib, wrapped_quib):
    assert np.array_equal(proxy_quib.get_value(), wrapped_quib.get_value())


@pytest.mark.regression
def test_proxy_quib_reverse_assigns(proxy_quib, wrapped_quib):
    (proxy_quib + 1)[0] = 2

    assert wrapped_quib.get_value()[0] == 1

