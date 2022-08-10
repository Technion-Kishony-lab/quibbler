import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.function_overriding.function_override import NotImplementedFunc


def test_function_defined_as_unimplemented_does_runs_on_non_quibs(axes):
    axes.axis([0, 7, 0, 5])
    assert np.array_equal(axes.get_xlim(), [0, 7])
    assert np.array_equal(axes.get_ylim(), [0, 5])


def test_function_defined_as_unimplemented_raises_exception_on_quibs(axes):
    x = iquib(7)
    with pytest.raises(NotImplementedFunc, match='.*'):
        axes.grid(x)
