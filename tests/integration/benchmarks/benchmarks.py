import pytest
from pyquibbler import iquib, q
from matplotlib import pyplot as plt
import numpy as np


@pytest.mark.benchmark()
def test_speed_iquib_creation(benchmark):
    benchmark(iquib, 1.)


@pytest.mark.benchmark()
def test_speed_fquib_creation(benchmark):
    a = iquib(1.)
    benchmark(np.sin, a)


@pytest.mark.benchmark()
def test_speed_get_shape(benchmark):
    a = iquib(1.)
    b = np.sin(a)
    benchmark(lambda: b.get_shape())


@pytest.mark.benchmark()
def test_speed_get_value(benchmark):
    a = iquib(1.)
    b = np.sin(a)
    benchmark(lambda: b.get_value())


@pytest.mark.benchmark()
def test_speed_create_graphics(benchmark, axes):
    a = iquib(np.array([1., 2., 3., 4.]))
    benchmark(lambda: axes.plot(a))


@pytest.mark.benchmark()
def test_speed_refresh_graphics(benchmark, axes):
    a = iquib(np.array([1., 2., 3., 4.]))
    axes.plot(a)
    benchmark(lambda: a.assign(0.5, 1))

