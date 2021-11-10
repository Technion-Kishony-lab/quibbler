from unittest import mock

from pyquibbler.project import Project
from pyquibbler.quib import ImpureFunctionQuib, GraphicsFunctionQuib


def test_get_or_create_only_creates_one_instance():
    assert Project.get_or_create() is Project.get_or_create()


def test_reset_impure_function_quibs_clears_their_cache():
    func = mock.Mock()
    func.side_effect = [1, 2]
    quib = ImpureFunctionQuib.create(func=func)
    assert quib.get_value() == 1, "sanity"
    assert quib.get_value() == 1, "sanity"

    Project.get_or_create().reset_invalidate_and_redraw_all_impure_function_quibs()

    assert quib.get_value() == 2


def test_reset_impure_function_quibs_invalidates_and_redraws():
    func = mock.Mock()
    func.side_effect = [1, 2]
    quib = ImpureFunctionQuib.create(func=func)
    quib.get_value()
    graphics_function_mock = mock.Mock()
    _ = GraphicsFunctionQuib.create(func=graphics_function_mock, func_args=(quib,), lazy=True)

    Project.get_or_create().reset_invalidate_and_redraw_all_impure_function_quibs()

    graphics_function_mock.assert_called_once_with(2)