import weakref
from unittest import mock

import pytest

from pyquibbler import iquib, Assignment
from pyquibbler.file_syncing import SaveFormat
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.graphics import dragging
from pyquibbler.project import Project, NothingToUndoException, NothingToRedoException
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics import GraphicsUpdateType
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException, UnknownEnumException, \
    InvalidArgumentValueException


def test_get_or_create_only_creates_one_instance():
    assert Project.get_or_create() is Project.get_or_create()


@pytest.fixture()
def random_func_with_side_effect():
    func = mock.Mock()
    func.side_effect = [1, 2]
    add_definition_for_function(func=func, func_definition=create_func_definition(is_random=True))
    return func


def test_reset_impure_quibs_clears_their_cache(random_func_with_side_effect):
    quib = create_quib(func=random_func_with_side_effect)
    assert quib.get_value() == 1, "sanity"
    assert quib.get_value() == 1, "sanity"

    Project.get_or_create().reset_random_quibs()

    assert quib.get_value() == 2


def test_reset_impure_quibs_invalidates_and_redraws(random_func_with_side_effect):
    quib = create_quib(func=random_func_with_side_effect)
    quib.get_value()
    graphics_function_mock = mock.Mock()
    add_definition_for_function(graphics_function_mock, create_func_definition(is_graphics=True, lazy=True))
    _ = create_quib(func=graphics_function_mock, args=(quib,))

    Project.get_or_create().reset_random_quibs()

    assert graphics_function_mock.call_count == 1


def test_undo_assignment(project):
    a = iquib(10)
    a.assign(1)
    assert a.get_value() == 1, "sanity"

    project.undo()

    assert a.get_value() == 10


def test_undo_assignment_with_multiple_assignments_in_same_path(project):
    a = iquib(10)
    a.assign(1)
    a.assign(2)
    assert a.get_value() == 2, "sanity"

    project.undo()

    assert a.get_value() == 1


def test_undo_multiple_assignments(project):
    a = iquib(10)
    a.assign(1)
    a.assign(2)
    assert a.get_value() == 2, "sanity"

    project.undo()
    project.undo()

    assert a.get_value() == 10


def test_undo_too_much_raises_exception(project):
    a = iquib(10)
    a.assign(1)

    project.undo()
    with pytest.raises(NothingToUndoException):
        project.undo()


def test_undo_redo(project):
    a = iquib(5)
    a.assign(1)

    project.undo()
    assert a.get_value() == 5, "sanity"
    project.redo()

    assert a.get_value() == 1


def test_undo_redo_undo(project):
    a = iquib(5)
    a.assign(1)
    a.assign(2)

    project.undo()
    project.redo()
    project.undo()

    assert a.get_value() == 1


def test_undo_assignment_removal(project):
    a = iquib(5)
    a.assign(10)
    a.handler.remove_override([])
    assert a.get_value() == 5, "sanity"

    project.undo()

    assert a.get_value() == 10


def test_undo_assignment_removal_and_assignment(project):
    a = iquib(5)
    a.assign(10)
    a.handler.remove_override([])
    assert a.get_value() == 5, "sanity"

    project.undo()
    project.undo()

    assert a.get_value() == 5


@pytest.mark.regression
def test_undo_with_multiple_paths(project):
    a = iquib([1, 2, 3, 4])
    a[0] = 5
    a[1] = 7

    project.undo()
    project.undo()

    assert a[0].get_value() == 1
    assert a[1].get_value() == 2


@pytest.mark.regression
def test_undo_redo_with_assignment_in_the_middle(project):
    a = iquib(10)
    a.assign(11)
    project.undo()
    a.assign(12)

    with pytest.raises(NothingToRedoException):
        project.redo()


def test_doesnt_record_when_dragging(project):
    a = iquib(5)
    with dragging():
        a.assign(10)

    with pytest.raises(NothingToUndoException):
        project.undo()


def test_project_undo_group_doesnt_add_on_dragging(project):
    a = iquib(5)
    with dragging():
        with project.start_undo_group():
            a.assign(10)
            a.assign(8)

    with pytest.raises(NothingToUndoException):
        project.undo()


def test_project_undo_with_group_reverts_back_to_before_group_and_runs_graphics_quib_once(project):
    a = iquib(5)
    mock_func = mock.Mock()
    add_definition_for_function(mock_func, create_func_definition(is_graphics=True))
    _ = create_quib(func=mock_func, args=(a,), lazy=False)
    with project.start_undo_group():
        a.handler.override(Assignment(
            path=[],
            value=10
        ))
        a.handler.override(Assignment(
            path=[],
            value=8
        ))
    count = mock_func.call_count

    project.undo()

    assert a.get_value() == 5
    assert mock_func.call_count == count + 1


def test_project_has_undo_when_not(project):
    assert project.can_undo() is False


def test_project_has_redo_when_not(project):
    assert project.can_redo() is False


def test_project_has_undo_when_true(project):
    a = iquib(1)
    a.assign(1)

    assert project.can_undo()


def test_project_has_redo_when_true(project):
    a = iquib(1)
    a.assign(1)
    project.undo()

    assert project.can_redo()


def test_project_redraw_central_graphics_function_quibs(project):
    func = mock.Mock()
    _ = create_quib(func=func, graphics_update='central', lazy=True)

    project.refresh_graphics()

    func.assert_called_once()


@pytest.mark.regression
def test_undo_redo_does_not_hold_strong_ref():
    a = iquib(7)
    mock_weakref_callback = mock.Mock()
    _ = weakref.ref(a, mock_weakref_callback)
    a.assign(10)

    del a

    mock_weakref_callback.assert_called_once()


@pytest.mark.regression
def test_undo_redos_clear_from_stack_on_removal(project):
    a = iquib(7)
    a.assign(10)
    assert project.can_undo(), "sanity"

    del a

    assert not project.can_undo()


@pytest.mark.parametrize(['prop_name', 'set_value', 'get_value'], [
    ('save_format', 'off', SaveFormat.OFF),
    ('save_format', SaveFormat.VALUE_TXT, SaveFormat.VALUE_TXT),
    ('graphics_update', 'never', GraphicsUpdateType.NEVER),
    ('directory', '/my_folder', PathWithHyperLink('/my_folder')),
    ('directory', None, None),
])
def test_project_correctly_set_valid_values(project, prop_name, set_value, get_value):
    setattr(project, prop_name, set_value)
    assert getattr(project, prop_name) == get_value


@pytest.mark.parametrize(['prop_name', 'set_value', 'exception'], [
    ('save_format', None, InvalidArgumentTypeException),
    ('save_format', 2, InvalidArgumentTypeException),
    ('save_format', 'abc', UnknownEnumException),
    ('graphics_update', True, InvalidArgumentTypeException),
    ('directory', 7, InvalidArgumentTypeException),
])
def test_project_reject_set_invlid_properties(project, prop_name, set_value, exception):
    with pytest.raises(exception):
        setattr(project, prop_name, set_value)


@pytest.mark.regression
def test_undo_when_something_changed_at_inexact_path(project):
    quib = iquib([1, 2, 3])
    quib[0] = 4
    quib[0:2] = [0, 0]
    quib[0] = 6

    project.undo()

    assert quib.get_value() == [0, 0, 3]
