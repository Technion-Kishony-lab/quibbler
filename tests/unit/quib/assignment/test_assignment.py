from pyquibbler.quib.assignment import Assignment


def test_assignment_apply():
    data = [0]
    Assignment(0, 1).apply(data)

    assert data == [1]


def test_assignment_apply_with_assignment_template(assignment_template_mock):
    data = [0]
    Assignment(0, 1).apply(data, assignment_template_mock)

    assert data == [assignment_template_mock.convert.return_value]
