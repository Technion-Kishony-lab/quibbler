from unittest.mock import Mock


def get_mock_with_repr(repr_value: str):
    mock = Mock()
    mock.__repr__ = Mock(return_value=repr_value)
    return mock


slicer = type('Slicer', (), dict(__getitem__=lambda self, item: item))()
