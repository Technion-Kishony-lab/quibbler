import matplotlib.pyplot as plt
import numpy as np

from unittest import mock
from unittest.mock import Mock

import pytest

from pyquibbler import iquib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from weakref import ref


def test_quibs_deleted_when_variable_clears():
    a = iquib(1)
    b = a + 2
    ref_a = ref(a)
    ref_b = ref(b)
    del a, b

    assert ref_a() is None
    assert ref_b() is None


def test_plot_quibs_persist_on_artist(axes):
    a = iquib(1)
    plot_quib = axes.plot(1, a)
    ref_plot_quib = ref(plot_quib)

    del plot_quib
    assert ref_plot_quib() is not None


def test_vectorize_plot_quibs_persist_on_artist(axes):
    a = iquib([1, 2])
    plot_quib = None

    def plot_point(x):
        nonlocal plot_quib
        plot_quib = axes.plot(x, x)

    vectorize_plot_point = np.vectorize(plot_point, signature='()->()', pass_quibs=True, is_graphics=True)
    vectorize_plot_quib = vectorize_plot_point(a)

    ref_plot_quib = ref(plot_quib)
    ref_vectorize_plot_quib = ref(vectorize_plot_quib)

    del plot_quib
    del vectorize_plot_quib

    assert ref_plot_quib() is not None
    assert ref_vectorize_plot_quib() is not None
