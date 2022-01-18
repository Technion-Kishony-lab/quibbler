import numpy as np

from pyquibbler import iquib
from pyquibbler.quib.graphics import GraphicsFuncQuib


def test_holistic_function_quib_with_numpy_applier():
    argument = iquib([0, 1, 2])

    res = np.apply_along_axis(lambda x: x, 0, argument)

    assert list(res.get_value()) == [0, 1, 2]
    assert isinstance(res, GraphicsFuncQuib)


def test_holistic_function_quib_with_numpy_applier_and_quib_change():
    argument = iquib([0, 1, 2])

    quib = np.apply_along_axis(lambda x: x, 0, argument)
    argument[0] = 10

    assert list(quib.get_value()) == [10, 1, 2]
