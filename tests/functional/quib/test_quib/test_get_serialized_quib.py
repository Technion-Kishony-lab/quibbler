from pyquibbler import iquib
from pyquibbler.project.jupyer_project.utils import get_serialized_quib
import numpy as np


def test_get_serialized_quib_with_a_multi_line_assignment():
    a = iquib(1)
    a.assign(np.array([[1, 2],
                       [3, 4]]))
    serialized = get_serialized_quib(a)
    assert serialized['overrides'][0]['right'] == 'array([[1, 2],\n       [3, 4]])'
