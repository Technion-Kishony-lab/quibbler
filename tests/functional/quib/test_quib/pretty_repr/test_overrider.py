import numpy as np
import pytest

from pyquibbler.quib.specialized_functions.iquib import iquib


@pytest.mark.parametrize("assignments", [
    ["a[1] = 3"],
    ["a[:, 0] = 1"],
    ["a[0] = 1", "a[0, 1] = 2"]
])
@pytest.mark.get_variable_names(True)
def test_overrider_pretty_repr_array_assignments(assignments):
    data = np.array([[1, 2, 3]])
    a = iquib(data)
    for assignment in assignments:
        exec(assignment)
    expected = "a = iquib(array([[1, 2, 3]]))" + f"\n" + f"\n".join(assignments)
    assert repr(a) == expected

@pytest.mark.parametrize("assignments", [
    ["a['name'] = 'Wow'"],
    ["a['short_name'] = 'quib'"],
    ["a['numbers'] = [1, 2, 3]", "a['numbers'][1] = 20"],
])
@pytest.mark.get_variable_names(True)
def test_overrider_pretty_repr_dict_assignments(assignments):
    data = {'name': 'Quibbler'}
    a = iquib(data)
    for assignment in assignments:
        exec(assignment)
    expected = "a = iquib({'name': 'Quibbler'})" + f"\n" + f"\n".join(assignments)
    assert repr(a) == expected

