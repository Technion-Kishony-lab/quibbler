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
