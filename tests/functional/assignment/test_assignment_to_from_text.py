import numpy as np
import pytest

from pyquibbler import default, Assignment
from pyquibbler.assignment.assignment_to_from_text \
    import convert_simplified_text_to_assignment, convert_assignment_to_simplified_text
from pyquibbler.assignment.exceptions import CannotConvertTextToAssignmentsException
from pyquibbler.path import PathComponent


@pytest.mark.parametrize(['override_text', 'expected_path', 'expected_value'], [
    ('[1] = 0', [1], 0),
    ('   [1] =0  ', [1], 0),
    (' "=0"', [], "=0"),
    (' = "wow"', [], "wow"),
    (' = array([1])', [], np.array([1])),
    (' = default', [], default),
    (" ['b'][1] =  3.14", ['b', 1], 3.14),
])
def test_convert_simplified_text_to_assignment(override_text, expected_path, expected_value):
    assignment = convert_simplified_text_to_assignment(override_text)
    assert [component.component for component in assignment.path] == expected_path
    assert assignment.value == expected_value


@pytest.mark.parametrize(['override_text'], [
    ("hi there",),
    ("[] = 7",),
])
def test_cannot_convert_simplified_text_to_assignment(override_text):
    with pytest.raises(CannotConvertTextToAssignmentsException, match='.*'):
        convert_simplified_text_to_assignment(override_text)


@pytest.mark.parametrize(['components', 'value', 'expected_text'], [
    ([1], 0, '[1] = 0'),
    ([], "hello", "= 'hello'"),
    ([], np.array([2]), '= array([2])'),
    ([(1, slice(None, None, None)), np.array([False, True])], default, '[1, :][array([False,  True])] = default'),
])
def test_convert_assignment_to_simplified_text(components, value, expected_text):
    assignment = Assignment(path=[PathComponent(component) for component in components],
                            value=value)
    assert convert_assignment_to_simplified_text(assignment) == expected_text
