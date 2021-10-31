from unittest import mock

import pytest

from pyquibbler.quib import Quib


@pytest.fixture()
def create_mock_quib():
    def _create(shape, get_value_result):
        mock_quib = mock.Mock(spec=Quib)
        mock_quib.get_value_valid_at_path.return_value = get_value_result
        mock_quib.get_shape.return_value.get_value.return_value = shape
        return mock_quib
    return _create
