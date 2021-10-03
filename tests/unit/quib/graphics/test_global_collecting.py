import pytest
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from pyquibbler import iquib
from pyquibbler.quib.graphics import override_axes_methods
from pyquibbler.quib.graphics import global_collecting


@pytest.mark.parametrize("data", [
    [1, 2, 3],
    iquib([1, 2, 3])
])
def test_global_graphics_collecting_mode_happy_flow(axes, data):
    override_axes_methods()

    with global_collecting.global_graphics_collecting_mode():
        plt.plot(data)
    artists_created = global_collecting.get_artists_collected()

    assert len(artists_created) == 1
    assert isinstance(artists_created[0], Line2D)
