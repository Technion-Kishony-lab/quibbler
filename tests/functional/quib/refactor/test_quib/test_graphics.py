from unittest import mock

import pytest
from matplotlib.artist import Artist

from pyquibbler.graphics import global_collecting
from pyquibbler.quib.refactor.factory import create_quib


@pytest.fixture
def mock_artist():
    return mock.Mock(spec=Artist)


def create_artist(*args):
    return Artist()


def test_quib_func_creates_graphics_returns_true_if_created_graphics():
    global_collecting.OVERRIDDEN_GRAPHICS_FUNCTIONS_RUNNING = 1
    parent = create_quib(
        func=mock.Mock()
    )
    quib = create_quib(
        func=create_artist,
        args=(parent,)
    )
    assert quib.func_creates_graphics is False, "Sanity"
    quib.get_value()  # We should now know we create graphics

    assert quib.func_creates_graphics
