import pytest

from ...conftest import plt_show
from pyquibbler import iquib, q
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


@pytest.mark.benchmark()
def test_speed_drag(benchmark, axes, create_axes_mouse_press_move_release_events):
    from pyquibbler import timeit

    import matplotlib as mpl

    # backend = 'TkAgg'
    # backend = 'macosx'
    # mpl.use(backend)

    y = iquib([1., 2., 3.])
    h = axes.plot([1, 2, 3], y, 'o-')

    plt_show(block=False)

    def move_marker_with_mouse():
        create_axes_mouse_press_move_release_events(
            [
                (2., 2.),
                (2., 2.1),
                (2., 2.2),
                (2., 2.3),
                (2., 2.4),
                (2., 2.5),
                (2., 2.6),
                (2., 2.7),
                (2., 2.8),
                (2., 2.9),
                (2., 3.0),
            ],
            pause=0.001,
        )

    with timeit('local') as t:
        benchmark(move_marker_with_mouse)

    print(f'\n{t.total_time :.3f}')
    # master (78eb33db2baee825d9762fabab83cc143afc307e):
    # default -> 2.23 s
    # TkAgg -> 1.34 s
    # macos -> 1.34 s
