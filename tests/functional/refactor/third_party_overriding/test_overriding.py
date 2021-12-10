from unittest import mock

import pytest

from pyquibbler.overriding import get_definition_for_function, CannotFindDefinitionForFunctionException


def test_get_definition_for_function_with_unknown_function_raises_exception():
    with pytest.raises(CannotFindDefinitionForFunctionException):
        get_definition_for_function(mock.MagicMock(__name__="unknown_func"))
