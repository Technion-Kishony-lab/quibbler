import matplotlib.pyplot as plt
import pytest

from pyquibbler import override_all, iquib


@pytest.mark.regression
def test_graphics_function_quib_doesnt_fail_on_removal_of_artists(axes):
    override_all()
    input_quib = iquib([1, 2, 3])
    plt.plot(input_quib)
    plt.cla()

    input_quib[0] = 10


def test_graphics_function_quib_copy_color():
    override_all()
    input_quib = iquib([1., 2., 3.])
    plot_quib = plt.plot(input_quib)
    clr1 = plot_quib.get_value()[0].get_color()
    input_quib[1] = 0.
    clr2 = plot_quib.get_value()[0].get_color()
    assert(clr1 == clr2)


def test_graphics_function_quib_does_not_copy_color():
    override_all()
    input_quib = iquib([1., 2., 3.])
    clr = iquib([1, 0, 0])
    plot_quib = plt.plot(input_quib, color=clr)
    clr1 = plot_quib.get_value()[0].get_color()
    clr[1] = 1
    clr2 = plot_quib.get_value()[0].get_color()
    assert(clr1 == [1, 0, 0])
    assert(clr2 == [1, 1, 0])


