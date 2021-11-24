from unittest import mock

import pytest

from pyquibbler.quib.refactor.quib import Quib


def test_quib_invalidate_and_redraw_calls_children_with_graphics():
    quib = Quib(
        func=mock.Mock(),
        args=tuple(),
        kwargs={},
        allow_overriding=False,
        assignment_template=None,
        cache_behavior=None,
        is_known_graphics_func=False
    )

    graphics_quib = Quib.create(
        func=mock.Mock(),
        args=(quib,),
        kwargs={},
        is_known_graphics_func=True
    )

    quib.invalidate_and_redraw_at_path()

    graphics_quib.func.assert_called_once()