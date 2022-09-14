import weakref
from unittest import mock

import pytest

import pyquibbler as qb
from pyquibbler import iquib, Assignment, default
from pyquibbler.file_syncing import SaveFormat
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.project import Project, NothingToUndoException, NothingToRedoException
from pyquibbler.project.exceptions import NoProjectDirectoryException
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics import GraphicsUpdateType, aggregate_redraw_mode
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException, UnknownEnumException


def test_get_or_create_only_creates_one_instance():
    assert Project.get_or_create() is Project.get_or_create()


@pytest.fixture()
def random_func_with_side_effect():
    func = mock.Mock()
    func.side_effect = [1, 2]
    add_definition_for_function(func=func, func_definition=create_func_definition(is_random=True))
    return func


@pytest.fixture()
def file_loading_func_with_side_effect():
    func = mock.Mock()
    func.side_effect = [1, 2]
    add_definition_for_function(func=func, func_definition=create_func_definition(is_file_loading=True))
    return func


def test_project_raises_on_missing_directory(project):
    project.directory = None
    with pytest.raises(NoProjectDirectoryException, match='.*'):
        project.save_quibs()


def test_quib_added_to_project_when_created(project):
    quib = iquib(1)
    assert quib in project.quibs


def test_quib_removed_from_project_when_deleted(project):
    quib = iquib(1)
    assert len(project.quibs) == 1,  "sanity"
    del quib
    assert len(project.quibs) == 0


def test_reset_random_quibs_clears_their_cache(random_func_with_side_effect):
    quib = create_quib(func=random_func_with_side_effect)
    assert quib.get_value() == 1, "sanity"
    assert quib.get_value() == 1, "sanity"

    qb.reset_random_quibs()

    assert quib.get_value() == 2


def test_reset_file_loading_quibs_clears_their_cache(file_loading_func_with_side_effect):
    quib = create_quib(func=file_loading_func_with_side_effect)
    assert quib.get_value() == 1, "sanity"
    assert quib.get_value() == 1, "sanity"

    qb.reset_file_loading_quibs()

    assert quib.get_value() == 2


def test_reset_impure_quibs_invalidates_and_redraws(random_func_with_side_effect):
    quib = create_quib(func=random_func_with_side_effect)
    quib.get_value()
    graphics_function_mock = mock.Mock()
    add_definition_for_function(graphics_function_mock, create_func_definition(is_graphics=True))
    _ = create_quib(func=graphics_function_mock, args=(quib,))
    assert graphics_function_mock.call_count == 1, "sanity"

    qb.reset_impure_quibs()
    assert graphics_function_mock.call_count == 2


def test_undo_assignment():
    a = iquib(10)
    a.assign(1)
    assert a.get_value() == 1, "sanity"

    qb.undo()

    assert a.get_value() == 10


def test_undo_assignment_with_multiple_assignments_in_same_path():
    a = iquib(10)
    a.assign(1)
    a.assign(2)
    assert a.get_value() == 2, "sanity"

    qb.undo()

    assert a.get_value() == 1


def test_undo_multiple_assignments():
    a = iquib(10)
    a.assign(1)
    a.assign(2)
    assert a.get_value() == 2, "sanity"

    qb.undo()
    qb.undo()

    assert a.get_value() == 10


def test_undo_too_much_raises_exception():
    a = iquib(10)
    a.assign(1)

    qb.undo()
    with pytest.raises(NothingToUndoException, match='.*'):
        qb.undo()


def test_undo_redo():
    a = iquib(5)
    a.assign(1)

    qb.undo()
    assert a.get_value() == 5, "sanity"
    qb.redo()

    assert a.get_value() == 1


def test_undo_redo_undo():
    a = iquib(5)
    a.assign(1)
    a.assign(2)

    qb.undo()
    qb.redo()
    qb.undo()

    assert a.get_value() == 1


def test_undo_assignment_removal():
    a = iquib(5)
    a.assign(10)
    a.assign(default)
    assert a.get_value() == 5, "sanity"

    qb.undo()

    assert a.get_value() == 10


def test_undo_assignment_removal_and_assignment():
    a = iquib(5)
    a.assign(10)
    a.assign(default)
    assert a.get_value() == 5, "sanity"

    qb.undo()
    qb.undo()

    assert a.get_value() == 5


@pytest.mark.regression
def test_undo_with_multiple_paths():
    a = iquib([1, 2, 3, 4])
    a[0] = 5
    a[1] = 7

    qb.undo()
    qb.undo()

    assert a[0].get_value() == 1
    assert a[1].get_value() == 2


@pytest.mark.regression
def test_undo_redo_with_assignment_in_the_middle():
    a = iquib(10)
    a.assign(11)
    qb.undo()
    a.assign(12)

    with pytest.raises(NothingToRedoException, match='.*'):
        qb.redo()


def test_undo_inverse_assign_override_group():
    a = iquib(5)
    b = a + 10
    c = b * 2
    c.assign(32)
    assert a.get_value() == 6
    assert c.get_value() == 32

    qb.undo()
    assert a.get_value() == 5
    assert c.get_value() == 30


def test_project_undo_with_group_reverts_back_to_before_group_and_runs_graphics_quib_once(project):
    a = iquib(5)
    mock_func = mock.Mock()
    add_definition_for_function(mock_func, create_func_definition(is_graphics=True))
    _ = create_quib(func=mock_func, args=(a,), lazy=False)
    project.start_pending_undo_group()
    with aggregate_redraw_mode(is_dragging=True):
        a.handler.override(Assignment(
            path=[],
            value=10
        ))
        a.handler.override(Assignment(
            path=[],
            value=8
        ))
    project.push_pending_undo_group_to_undo_stack()
    count = mock_func.call_count

    project.undo()

    assert a.get_value() == 5
    assert mock_func.call_count == count + 1


def test_project_has_undo_when_not():
    assert qb.can_undo() is False


def test_project_has_redo_when_not():
    assert qb.can_redo() is False


def test_project_has_undo_when_true():
    a = iquib(1)
    a.assign(1)

    assert qb.can_undo()


def test_project_has_redo_when_true():
    a = iquib(1)
    a.assign(1)
    qb.undo()

    assert qb.can_redo()


def test_project_redraw_central_graphics_function_quibs():
    func = mock.Mock()
    _ = create_quib(func=func, graphics_update='central', lazy=True)

    qb.refresh_graphics()

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
def test_undo_redos_clear_from_stack_on_removal():
    a = iquib(7)
    a.assign(10)
    assert qb.can_undo(), "sanity"

    del a

    assert not qb.can_undo()


@pytest.mark.parametrize(['prop_name', 'set_value', 'get_value'], [
    ('save_format', 'off', SaveFormat.OFF),
    ('save_format', SaveFormat.TXT, SaveFormat.TXT),
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
def test_project_reject_set_invalid_properties(project, prop_name, set_value, exception):
    with pytest.raises(exception, match='.*'):
        setattr(project, prop_name, set_value)


@pytest.mark.regression
def test_undo_when_something_changed_at_inexact_path():
    quib = iquib([1, 2, 3])
    quib[0] = 4
    quib[0:2] = [0, 0]
    quib[0] = 6

    qb.undo()

    assert quib.get_value() == [0, 0, 3]


@pytest.mark.regression
def test_undo_after_undo():
    quib = iquib(1)
    quib.assign(3)
    qb.undo()
    quib.assign(4)

    qb.undo()

    assert quib.get_value() == 1


@pytest.mark.regression
def test_undo_after_remove_assignment(project):
    quib = iquib(1)
    quib.assign(3)
    project.remove_assignment_from_quib(quib=quib, assignment_index=0)
    # Sanity
    assert quib.get_value() == 1

    project.undo()

    assert quib.get_value() == 3


def test_set_project_directory_affects_quib_directory(project):
    quib = iquib(1)
    project.directory = 'test'
    assert(str(quib.actual_save_directory).endswith('test'))
    project.directory = None
    assert quib.actual_save_directory is None
