from unittest import mock

import pytest

from pyquibbler.refactor.quib.quib import Quib


@pytest.fixture()
def create_mock_quib():
    def _create(shape=None, get_value_result=None, children=None):
        shape = shape or (3, 1)
        get_value_result = get_value_result or [[1, 2, 3]]
        mock_quib = mock.Mock(spec=Quib)
        mock_quib.get_axeses.return_value = []
        mock_quib.get_value_valid_at_path.return_value = get_value_result
        mock_quib.get_shape.return_value = shape
        mock_quib.get_ndim.return_value = len(shape)
        mock_quib._get_children_recursively.return_value = children or set()
        return mock_quib
    return _create
