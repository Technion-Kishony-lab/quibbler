import pytest
from unittest import mock

from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib, CannotReverseUnknownFunctionException


def test_reverse_raises_exception_on_no_reverser_available():
    with pytest.raises(CannotReverseUnknownFunctionException):
        reverse_function_quib(
            function_quib=DefaultFunctionQuib.create(
                func=lambda: 1
            ),
            assignment=Assignment(value=0, paths=[0])
        )

#  All functionality tests reside per reverser in each of the sister modules in this package (they all still
#  go through `reverse_function_quib`)
