from unittest import mock

import pytest

from pyquibbler import iquib
from pyquibbler.project import Project
from pyquibbler.quib import ImpureFunctionQuib, GraphicsFunctionQuib
from pyquibbler.quib.action_stack import NothingToUndoException


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


def test_undo_assignment(project):
    a = iquib(10)
    a.assign_value(1)
    assert a.get_value() == 1, "sanity"

    project.undo()

    assert a.get_value() == 10


def test_undo_assignment_with_multiple_assignments_in_same_path(project):
    a = iquib(10)
    a.assign_value(1)
    a.assign_value(2)
    assert a.get_value() == 2, "sanity"

    project.undo()

    assert a.get_value() == 1


def test_undo_multiple_assignments(project):
    a = iquib(10)
    a.assign_value(1)
    a.assign_value(2)
    assert a.get_value() == 2, "sanity"

    project.undo()
    project.undo()

    assert a.get_value() == 10


def test_undo_too_much_raises_exception(project):
    a = iquib(10)
    a.assign_value(1)

    project.undo()
    with pytest.raises(NothingToUndoException):
        project.undo()

