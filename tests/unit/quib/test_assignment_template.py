from pytest import mark, raises

from pyquibbler.quib.assignment_template import BoundAssinmentTemplate, RangeAssignmentTemplate, \
    BoundMaxBelowMinException, RangeStopBelowStartException


@mark.parametrize(['template', 'data', 'expected'], [
    # Bound int
    (BoundAssinmentTemplate(0, 2), -1, 0),
    (BoundAssinmentTemplate(0, 2), 0, 0),
    (BoundAssinmentTemplate(0, 2), 1, 1),
    (BoundAssinmentTemplate(0, 2), 2, 2),
    (BoundAssinmentTemplate(0, 2), 3, 2),
    (BoundAssinmentTemplate(0, 2), 3, 2),

    # Bound float
    (BoundAssinmentTemplate(0.1, 0.2), 0., 0.1),
    (BoundAssinmentTemplate(0.1, 0.2), 0.15, 0.15),
    (BoundAssinmentTemplate(0.1, 0.2), 0.2, 0.2),

    # Range int
    (RangeAssignmentTemplate(-3, 3, 3), -7, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -4, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -3, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -2, -3),
    (RangeAssignmentTemplate(-3, 3, 3), -1, 0),
    (RangeAssignmentTemplate(-3, 3, 3), 0, 0),
    (RangeAssignmentTemplate(-3, 3, 3), 1, 0),
    (RangeAssignmentTemplate(-3, 3, 3), 2, 3),
    (RangeAssignmentTemplate(-3, 3, 3), 6, 3),
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
])
def test_casting_assignment_template(template, data, expected):
    result = template.convert(data)
    assert result == expected
    assert type(result) is type(expected)


def test_cant_create_bound_assignment_template_with_max_smaller_than_min():
    with raises(BoundMaxBelowMinException):
        BoundAssinmentTemplate(1., 0.9)


def test_cant_create_range_assignment_template_with_stop_smaller_than_start():
    with raises(RangeStopBelowStartException):
        RangeAssignmentTemplate(1., 0.9, 3.)
