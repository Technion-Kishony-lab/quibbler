from unittest import mock
from pytest import mark
from pyquibbler import iquib
from pyquibbler.quib.assignment.assignment import QuibWithAssignment


@mark.skip
def test_filter_quibs_with_assignments_when_one_quib_is_ancestor_of_another():
    q = iquib(3)
    function_quib = q + 5
    quibs_with_assignments = [QuibWithAssignment(
        quib=q,
        assignment=mock.Mock()
    ), QuibWithAssignment(
        quib=function_quib,
        assignment=mock.Mock()
    )]

    assert filter_quibs_with_assignments(quibs_with_assignments) == [quibs_with_assignments[0]]


@mark.skip
def test_filter_quibs_with_assignments_share_common_ancestor():
    q = iquib(3)
    function_quib = q + 5
    second_function_quib = q + 7
    quibs_with_assignments = [QuibWithAssignment(
        quib=function_quib,
        assignment=mock.Mock()
    ), QuibWithAssignment(
        quib=second_function_quib,
        assignment=mock.Mock()
    )]

    assert filter_quibs_with_assignments(quibs_with_assignments) == [quibs_with_assignments[0]]


@mark.skip
def test_filter_quibs_with_no_sharing():
    function_quib = iquib(2) + 8
    second_function_quib = iquib(3) + 5
    quibs_with_assignments = [QuibWithAssignment(
        quib=function_quib,
        assignment=mock.Mock()
    ), QuibWithAssignment(
        quib=second_function_quib,
        assignment=mock.Mock()
    )]

    assert filter_quibs_with_assignments(quibs_with_assignments) == quibs_with_assignments
