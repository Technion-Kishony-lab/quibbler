from unittest import mock

import pytest

from pyquibbler.inversion.invert import invert
from pyquibbler.path_translation.source_func_call import SourceFuncCall
from pyquibbler.utilities.multiple_instance_runner import NoRunnerWorkedException


def test_invert_raises_exception_on_unknown_func():
    assignment = mock.Mock()
    assignment.is_default = mock.Mock(return_value=False)

    with pytest.raises(NoRunnerWorkedException, match='.*'):
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
