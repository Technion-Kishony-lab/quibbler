from unittest import mock

import numpy as np
import pytest

from pyquibbler.quib.quib import Quib, QuibHandler


@pytest.fixture()
def create_mock_quib():
    def _create(shape=None, get_value_result=None, children=None):
        shape = shape or (3, 1)
        get_value_result = get_value_result or [[1, 2, 3]]
        mock_quib = mock.Mock(spec=Quib)
        mock_quib.get_value_valid_at_path.return_value = get_value_result
        mock_quib.get_shape.return_value = shape
        mock_quib.get_ndim.return_value = len(shape)
        mock_quib.handler = mock.Mock(spec=QuibHandler)
        mock_quib.handler.quib_function_call = mock.Mock()
        mock_quib.handler.quib_function_call.result_shape = np.shape(get_value_result)
        mock_quib.handler.quib_function_call.result_type = type(get_value_result)
        mock_quib.handler.get_figures.return_value = []
        mock_quib.pass_quibs = False
        mock_quib.is_proxy = False
        mock_quib.get_descendants.return_value = children or set()
        return mock_quib
    return _create


@pytest.fixture()
def mock_axes():
    axes = mock.Mock()
    axes.figure.canvas.supports_blit = False
    axes._children = []
    return axes
