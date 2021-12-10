from unittest import mock

import pytest

from pyquibbler.path_translators.exceptions import NoInvertersFoundException
from pyquibbler.path_translators import invert


def test_invert_raises_exception_on_unknown_func():
    with pytest.raises(NoInvertersFoundException):
        invert(
            func=mock.MagicMock(__name__='unknown'),
            args=tuple(),
            kwargs={},
            assignment=mock.Mock(),
            previous_result=0
        )
