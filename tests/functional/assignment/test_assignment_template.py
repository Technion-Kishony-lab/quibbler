import numpy as np
from typing import Any, Type
from pytest import mark, raises

from pyquibbler.assignment import AssignmentTemplate, BoundAssignmentTemplate, RangeAssignmentTemplate, \
    BoundMaxBelowMinException, RangeStopBelowStartException, TypesMustBeSameInAssignmentTemplateException
from pyquibbler.utilities.iterators import recursively_compare_objects_type


class ExampleAssignmentTemplate(AssignmentTemplate):
    def _convert_number(self, number: Any):
        return -number

    def _get_number_type(self) -> Type:
        return int


@mark.parametrize(['data', 'expected'], [
    (1, -1),
    ([1], [-1]),
    ([[1, 2], [3, 4]], [[-1, -2], [-3, -4]]),
    ((1,), (-1,)),
])
def test_assignment_template_convert(data, expected):
    assert ExampleAssignmentTemplate().convert(data) == expected


@mark.parametrize(['template', 'data', 'expected'], [
    (BoundAssignmentTemplate(0, 2), np.array([-1., 0, 1.7, 2, 3]), np.array([0, 0, 1, 2, 2])),
    (BoundAssignmentTemplate(0, 2), [-1., 0, 1.7, 2, 3], [0, 0, 1, 2, 2]),
    (BoundAssignmentTemplate(0, 2), [-1, 0, 1.7, [-1, 1.7, 10], 3], [0, 0, 1, [0, 1, 2], 2]),
    (BoundAssignmentTemplate(0, 2), {'a': 3, 'b': -1}, {'a': 2, 'b': 0}),

    # Bound int
    (BoundAssignmentTemplate(0, 2), -1, 0),
    (BoundAssignmentTemplate(0, 2), 0, 0),
    (BoundAssignmentTemplate(0, 2), 1, 1),
    (BoundAssignmentTemplate(0, 2), 2, 2),
    (BoundAssignmentTemplate(0, 2), 3, 2),

    # Bound float
    (BoundAssignmentTemplate(0.1, 0.2), 0., 0.1),
    (BoundAssignmentTemplate(0.1, 0.2), 0.15, 0.15),
    (BoundAssignmentTemplate(0.1, 0.2), 0.2, 0.2),
    (BoundAssignmentTemplate(0.1, 0.25), 0.2, 0.2),

    # Range int
    (RangeAssignmentTemplate(-3, 3, 3), -7, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -4, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -3, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -2, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -1, 0),
    (RangeAssignmentTemplate(-3, 3, 3), 0, 0),
    (RangeAssignmentTemplate(-3, 3, 3), 1, 0),
    (RangeAssignmentTemplate(-3, 3, 3), 2, 3),
    (RangeAssignmentTemplate(-3, 3, 3), 3, 3),
    (RangeAssignmentTemplate(-3, 3, 3), 10, 3),

    # Range when stop is not divisible by step
    (RangeAssignmentTemplate(0, 10, 4), 7, 8),
    (RangeAssignmentTemplate(0, 10, 4), 8, 8),
    (RangeAssignmentTemplate(0, 10, 4), 9, 8),
    (RangeAssignmentTemplate(0, 10, 4), 10, 8),
    (RangeAssignmentTemplate(0, 10, 4), 11, 8),
    (RangeAssignmentTemplate(0, 10, 4), 12, 8),
    (RangeAssignmentTemplate(0, 10, 4), 13, 8),

    # Range when step > stop - start
    (RangeAssignmentTemplate(1, 10, 15), -110, 1),
    (RangeAssignmentTemplate(1, 10, 15), -5, 1),
    (RangeAssignmentTemplate(1, 10, 15), 1, 1),
    (RangeAssignmentTemplate(1, 10, 15), 9, 1),
    (RangeAssignmentTemplate(1, 10, 15), 10, 1),
    (RangeAssignmentTemplate(1, 10, 15), 15, 1),
    (RangeAssignmentTemplate(1, 10, 15), 110, 1),
    (RangeAssignmentTemplate(1, 1, 15), 110, 1),

    # Range float
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), -0.7, -0.3),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), -0.4, -0.3),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), -0.3, -0.3),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), -0.2, -0.3),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), -0.1, 0.0),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), 0.0, 0.),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), 0.1, 0.),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), 0.2, 0.3),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), 0.6, 0.3),
    (RangeAssignmentTemplate(-0.3, 0.4, 0.3), 1., 0.3),
    (RangeAssignmentTemplate(-0.3, -0.3, 0.3), 1., -0.3),

    # Regression - range ndarray
    (RangeAssignmentTemplate(np.array(-0.3), np.array(-0.3), np.array(0.3)), np.array(1.), np.array(-0.3)),

    # Regression- casts float
    (BoundAssignmentTemplate(1, 10), 1.7, 1),
])
def test_casting_assignment_template(template, data, expected):
    result = template.convert(data)
    if isinstance(result, np.ndarray):
        assert result.dtype == expected.dtype
        assert np.array_equal(result, expected)
    else:
        assert result == expected
        assert recursively_compare_objects_type(result, expected)


def test_cant_create_bound_assignment_template_with_max_smaller_than_min():
    with raises(BoundMaxBelowMinException, match='.*'):
        BoundAssignmentTemplate(1., 0.9)


def test_cant_create_range_assignment_template_with_stop_smaller_than_start():
    with raises(RangeStopBelowStartException, match='.*'):
        RangeAssignmentTemplate(1., 0.9, 3.)


def test_cant_create_bound_assignment_template_with_different_types():
    with raises(TypesMustBeSameInAssignmentTemplateException, match='.*'):
        BoundAssignmentTemplate(0, 1.)


def test_cant_create_range_assignment_template_with_different_types():
    with raises(TypesMustBeSameInAssignmentTemplateException, match='.*'):
        RangeAssignmentTemplate(0, 1, .1)
