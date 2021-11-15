from unittest import mock
from unittest.mock import Mock

from pytest import fixture


@fixture()
def mock_artist(monkeypatch):
    return mock.Mock()


@fixture
def assignment_template_mock():
    mock = Mock()
    mock.convert.return_value = object()
    return mock
