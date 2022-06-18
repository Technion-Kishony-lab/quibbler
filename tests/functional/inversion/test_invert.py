from unittest import mock

import pytest

from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.exceptions import NoInvertersFoundException
from pyquibbler.inversion.invert import invert
from pyquibbler.translation.source_func_call import SourceFuncCall


def test_invert_raises_exception_on_unknown_func():
    assignment = mock.Mock()
    assignment.is_default = mock.Mock(return_value=False)

    with pytest.raises(NoInvertersFoundException):
        invert(
            func_call=SourceFuncCall.from_(func=mock.MagicMock(__name__='unknown'),
                                           func_args=tuple(),
                                           func_kwargs={},
                                           include_defaults=True,
                                           data_source_locations=[],
                                           parameter_source_locations=[]
                                           ),
            assignment=assignment,
            previous_result=0
        )
