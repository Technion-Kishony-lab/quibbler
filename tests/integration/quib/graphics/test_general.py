import matplotlib.pyplot as plt
import pytest

from pyquibbler import initialize_quibbler, iquib, Quib, quiby
from pyquibbler.graphics.global_collecting import AxesCreatedDuringQuibEvaluationException


@pytest.mark.regression
def test_graphics_function_quib_doesnt_fail_on_removal_of_artists(axes):
    input_quib = iquib([1, 2, 3])
    plt.plot(input_quib)
    plt.cla()

    input_quib[0] = 10


@pytest.mark.regression
def test_graphics_quiby_function_doesnt_fail_when_creating_axes():
    def plot_draggable(y: Quib):
        plt.plot(y)

    plt.close("all")
    data = iquib([1, 2])
    with pytest.raises(AxesCreatedDuringQuibEvaluationException, match='.*'):
        quiby(plot_draggable, is_graphics=True)(data)
