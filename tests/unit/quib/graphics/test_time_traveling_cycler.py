from itertools import cycle

from pyquibbler.quib.graphics.time_traveling_cycler import TimeTravelingCycler


def test_time_traveling_cycler_without_reset():
    a = cycle([1, 2, 3])
    cycler = TimeTravelingCycler(a)

    first_value = next(cycler)
    second_value = next(cycler)

    assert first_value == 1
    assert second_value == 2


def test_time_traveling_cycler_with_reset():
    a = cycle([1, 2, 3])
    cycler = TimeTravelingCycler(a)

    first_value = next(cycler)
    cycler.reset()
    second_value = next(cycler)

    assert first_value == 1
    assert second_value == 1