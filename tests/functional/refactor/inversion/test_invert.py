from unittest import mock

import pytest

from pyquibbler.refactor.function_definitions.func_call import FuncCall
from pyquibbler.refactor.inversion.exceptions import NoInvertersFoundException
from pyquibbler.refactor.inversion.invert import invert


def test_invert_raises_exception_on_unknown_func():
    with pytest.raises(NoInvertersFoundException):
        invert(
            func_call=FuncCall.from_function_call(func=mock.MagicMock(__name__='unknown'),
                args=tuple(),
                kwargs={},
                include_defaults=True
            ),
            assignment=mock.Mock(),
            previous_result=0
        )
