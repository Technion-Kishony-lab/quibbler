import pytest
from unittest import mock

from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.reverse_assignment import get_reversals_for_assignment, \
    CannotReverseUnknownFunctionException


def test_reverse_raises_exception_on_no_reverser_available():
    with pytest.raises(CannotReverseUnknownFunctionException):
        get_reversals_for_assignment(
            function_quib=DefaultFunctionQuib.create(
                func=lambda: 1
            ),
            assignment=Assignment(value=0, paths=[0])
        )

#  All functionality tests reside per reverser in each of the sister modules in this package (they all still
#  go through `get_reversals_for_assignment`)
