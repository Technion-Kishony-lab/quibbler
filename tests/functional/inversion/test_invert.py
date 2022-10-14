from unittest import mock

import pytest

from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.exceptions import NoInvertersWorkedException
from pyquibbler.inversion.invert import invert
from pyquibbler.path_translation.source_func_call import SourceFuncCall


def test_invert_raises_exception_on_unknown_func():
    assignment = mock.Mock()
    assignment.is_default = mock.Mock(return_value=False)

    with pytest.raises(NoInvertersWorkedException, match='.*'):
        invert(
            func_call=SourceFuncCall.from_(func=mock.MagicMock(__name__='unknown'),
                                           func_args=tuple(),
                                           func_kwargs={},
                                           data_source_locations=[],
                                           parameter_source_locations=[]
                                           ),
            assignment=assignment,
            previous_result=0
        )
