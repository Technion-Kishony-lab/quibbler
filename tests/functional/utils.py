from unittest import mock
from unittest.mock import Mock
from dataclasses import dataclass, field
from typing import List

from pyquibbler.quib.quib import Quib
from pyquibbler.path import PathComponent, Path


def get_mock_with_repr(repr_value: str):
    mock = Mock()
    mock.__repr__ = Mock(return_value=repr_value)
    return mock


slicer = type('Slicer', (), dict(__getitem__=lambda self, item: item))()


@dataclass
class PathBuilder:
    quib: Quib
    path: Path = field(default_factory=list)

    def __getitem__(self, item):
        self.quib.get_type()  # legacy from when PathComponent had type
        return PathBuilder(self.quib[item], [*self.path, PathComponent(item)])


def get_func_mock(func):
    return mock.create_autospec(func, side_effect=func)
