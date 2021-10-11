from typing import List
from unittest.mock import Mock
import numpy as np
from pytest import raises, fixture

from pyquibbler import iquib
from pyquibbler.quib import get_overrides_for_assignment, CannotAssignException, DefaultFunctionQuib
from pyquibbler.quib.assignment import Assignment, QuibWithAssignment
from pyquibbler.quib.override_choice import override_choice as override_choice_module
from pyquibbler.quib.override_choice.override_dialog import OverrideChoice, OverrideChoiceType


class ChooseOverrideDialogMockSideEffect:
    def __init__(self, choice: OverrideChoice = None):
        self.choice = choice

    def __call__(self, options: List[QuibWithAssignment], can_diverge: bool):
        assert self.choice is not None, f'Choice for {self} not set before it was called'
        assert options, 'There is no reason to open a dialog without options'
        if self.choice.choice_type is OverrideChoiceType.OVERRIDE:
            assert self.choice.chosen_override in options, \
                f'Chose option {self.choice.chosen_override} which was not in {options}'
        elif self.choice.choice_type is OverrideChoiceType.DIVERGE:
            assert can_diverge, 'Chose to diverge but it is not an option'
        return self.choice


@fixture
def assignment():
    return Assignment(5, [...])


@fixture
def choose_override_dialog_mock():
    return Mock(side_effect=ChooseOverrideDialogMockSideEffect())


@fixture(autouse=True)
def override_choice_dialog(monkeypatch, choose_override_dialog_mock):
    overridden_name = 'choose_override_dialog'
    assert hasattr(override_choice_module, overridden_name), \
        f'This fixture assumes that the {override_choice_module.__name__} module imports {overridden_name}, ' \
        f'as the fixture tries to replace the function with a mock.'
    monkeypatch.setattr(override_choice_module, overridden_name, choose_override_dialog_mock)


def test_get_overrides_for_assignment_when_nothing_is_overridable(assignment):
    quib = iquib(1)
    quib.allow_overriding = False
    child = quib + 1

    with raises(CannotAssignException) as exc_info:
        get_overrides_for_assignment(child, assignment)
    assert exc_info.value.assignment is assignment
    assert exc_info.value.quib is child


def test_get_overrides_for_assignment_when_reverse_assignment_not_implemented(assignment):
    quib = iquib(1)
    child = DefaultFunctionQuib.create(lambda x: x, (quib,))
    assignment = Assignment(5, [...])

    with raises(CannotAssignException) as exc_info:
        get_overrides_for_assignment(child, assignment)
    assert exc_info.value.assignment is assignment
    assert exc_info.value.quib is child


def test_get_overrides_for_assignment_when_diverged_reverse_assign_has_only_one_overridable_child(assignment):
    quib1 = iquib([1])
    quib1.allow_overriding = False
    quib2 = iquib([2])
    concat = np.concatenate((quib1, quib2))
    child = concat + 1

    with raises(CannotAssignException) as exc_info:
        get_overrides_for_assignment(child, assignment)
    assert exc_info.value.assignment is assignment
    assert exc_info.value.quib is child


def test_get_overrides_for_assignment_on_iquib(assignment):
    quib = iquib(1)

    overrides = get_overrides_for_assignment(quib, assignment)

    assert overrides == [QuibWithAssignment(quib, assignment)]


def test_get_overrides_for_assignment_on_quib_without_overridable_parents(assignment):
    quib = iquib(1)
    quib.allow_overriding = False
    child = quib + 1
    child.allow_overriding = True

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [QuibWithAssignment(child, assignment)]


def test_get_overrides_for_assignment_on_non_overridable_quib_with_overridable_parent(assignment):
    parent = iquib(1)
    child = parent + 1

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [QuibWithAssignment(parent, Assignment(4, [...]))]


def test_get_overrides_for_assignment_with_choice_to_override_child(assignment, choose_override_dialog_mock):
    parent = iquib(1)
    child = parent + 1
    child.allow_overriding = True
    chosen_override = QuibWithAssignment(child, assignment)
    choose_override_dialog_mock.side_effect.choice = OverrideChoice(OverrideChoiceType.OVERRIDE, chosen_override)

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [chosen_override]
    choose_override_dialog_mock.assert_called_once()


def test_get_overrides_for_assignment_with_choice_to_override_parent(assignment, choose_override_dialog_mock):
    parent = iquib(1)
    child = parent + 1
    child.allow_overriding = True
    chosen_override = QuibWithAssignment(parent, Assignment(4, [...]))
    choose_override_dialog_mock.side_effect.choice = OverrideChoice(OverrideChoiceType.OVERRIDE, chosen_override)

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [chosen_override]
    choose_override_dialog_mock.assert_called_once()

# test caching, test diverged trees
