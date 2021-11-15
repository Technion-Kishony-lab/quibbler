from unittest import mock

import pytest

from pyquibbler import iquib
from pyquibbler.project import Project, NothingToUndoException
from pyquibbler.quib import ImpureFunctionQuib, GraphicsFunctionQuib
from pyquibbler.quib.graphics.widgets.drag_context_manager import dragging


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
    _ = GraphicsFunctionQuib.create(func=graphics_function_mock, func_args=(quib,))

    Project.get_or_create().reset_invalidate_and_redraw_all_impure_function_quibs()

    assert graphics_function_mock.call_count == 2


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


def test_undo_redo(project):
    a = iquib(5)
    a.assign_value(1)

    project.undo()
    assert a.get_value() == 5, "sanity"
    project.redo()

    assert a.get_value() == 1


def test_undo_redo_undo(project):
    a = iquib(5)
    a.assign_value(1)
    a.assign_value(2)

    project.undo()
    project.redo()
    project.undo()

    assert a.get_value() == 1


def test_undo_assignment_removal(project):
    a = iquib(5)
    a.assign_value(10)
    a.remove_override([])
    assert a.get_value() == 5, "sanity"

    project.undo()

    assert a.get_value() == 10


def test_undo_assignment_removal_and_assignment(project):
    a = iquib(5)
    a.assign_value(10)
    a.remove_override([])
    assert a.get_value() == 5, "sanity"

    project.undo()
    project.undo()

    assert a.get_value() == 5


def test_doesnt_record_when_dragging(project):
    a = iquib(5)
    with dragging():
        a.assign_value(10)

    with pytest.raises(NothingToUndoException):
        project.undo()


def test_project_undo_group_doesnt_add_on_dragging(project):
    a = iquib(5)
    with dragging():
        with project.start_undo_group():
            a.assign_value(10)
            a.assign_value(8)

    with pytest.raises(NothingToUndoException):
        project.undo()


def test_project_undo_with_group_reverts_back_to_before_group_and_runs_graphics_quib_once(project):
    a = iquib(5)
    mock_func = mock.Mock()
    _ = GraphicsFunctionQuib.create(func=mock_func, func_args=(a,))
    with project.start_undo_group():
        a.assign_value(10)
        a.assign_value(8)
    count = mock_func.call_count

    project.undo()

    assert a.get_value() == 5
    assert mock_func.call_count == count + 1


def test_project_has_undo_when_not(project):
    assert project.has_undo() is False


def test_project_has_redo_when_not(project):
    assert project.has_redo() is False


def test_project_has_undo_when_true(project):
    a = iquib(1)
    a.assign_value(1)

    assert project.has_undo()


def test_project_has_redo_when_true(project):
    a = iquib(1)
    a.assign_value(1)
    project.undo()

    assert project.has_redo()


def test_project_redraw_central_graphics_function_quibs(project):
    func = mock.Mock()
    _ = GraphicsFunctionQuib.create(func=func, update_type='central', evaluate_now=False)

    project.redraw_central_refresh_graphics_function_quibs()

    func.assert_called_once()

