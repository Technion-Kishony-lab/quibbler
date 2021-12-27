from unittest import mock

import pytest

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.refactor.inversion.invert import invert


# TODO: Do we want to raise an exception on unknown func?

@pytest.mark.skip("Make order in how this shit should fail")
def test_invert_raises_exception_on_unknown_func():
    with pytest.raises(PyQuibblerException):
        invert(
            func=mock.MagicMock(__name__='unknown'),
            args=tuple(),
            kwargs={},
            assignment=mock.Mock(),
            previous_result=0
        )
