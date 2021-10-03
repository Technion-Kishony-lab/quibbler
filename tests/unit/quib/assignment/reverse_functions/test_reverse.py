from unittest import mock

import pytest

from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib, CannotReverseUnknownFunctionException


def test_reverse_raises_exception_on_no_reverser_available():
    with pytest.raises(CannotReverseUnknownFunctionException):
        reverse_function_quib(
            function_quib=DefaultFunctionQuib.create(
                func=mock.Mock()
            ),
            indices=0,
            value=0
        )

#  All functionality tests reside per reverser in each of the sister modules in this package (they all still
#  go through `reverse_function_quib`)
