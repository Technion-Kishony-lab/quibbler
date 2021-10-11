import numpy as np
from typing import List
from unittest.mock import Mock
from pytest import raises, fixture

from pyquibbler import iquib
from pyquibbler.quib import get_overrides_for_assignment, CannotAssignException, DefaultFunctionQuib
from pyquibbler.quib.assignment import Assignment, QuibWithAssignment
from pyquibbler.quib.override_choice import override_choice as override_choice_module
from pyquibbler.quib.override_choice.override_dialog import OverrideChoice, OverrideChoiceType


class ChooseOverrideDialogMockSideEffect:
    def __init__(self):
        self.choices = []

    def add_choices(self, *choices):
        self.choices = [*self.choices, *choices]

    def __call__(self, options: List[QuibWithAssignment], can_diverge: bool):
        assert self.choices, 'The dialog mock was called more times than expected'
        choice, *self.choices = self.choices
        assert choice is not None, f'Choice for {self} not set before it was called'
        assert options, 'There is no reason to open a dialog without options'
        if choice.choice_type is OverrideChoiceType.OVERRIDE:
            assert choice.chosen_override in options, \
                f'Chose option {choice.chosen_override} which was not in {options}'
        elif choice.choice_type is OverrideChoiceType.DIVERGE:
            assert can_diverge, 'Chose to diverge but it is not an option'
        return choice

    def assert_all_choices_made(self):
        assert not self.choices, f'Not all choices were made, left with: {self.choices}'


@fixture
def assignment():
    return Assignment(5, [...])


@fixture(autouse=True)
def choose_override_dialog_mock():
    """
    This fixture is autouse, because if a dialog is erroneously invoked from a test,
    we want it to fail rather then open an actual dialog and block.
    """
    side_effect = ChooseOverrideDialogMockSideEffect()
    yield Mock(side_effect=side_effect)
    side_effect.assert_all_choices_made()


@fixture(autouse=True)
def override_choice_dialog(monkeypatch, choose_override_dialog_mock):
    overridden_name = 'choose_override_dialog'
    assert hasattr(override_choice_module, overridden_name), \
        f'This fixture assumes that the {override_choice_module.__name__} module imports {overridden_name}, ' \
        f'as the fixture tries to replace the function with a mock.'
    monkeypatch.setattr(override_choice_module, overridden_name, choose_override_dialog_mock)


@fixture
def parent_and_child():
    parent = iquib(1)
    child = parent + 1
    return parent, child


@fixture
def diverged_quib_graph():
    grandparent1 = iquib(np.array([1]))
    parent1 = grandparent1 * 1.
    grandparent2 = iquib(np.array([2]))
    parent2 = grandparent2 * 1.
    parent3 = iquib(np.array([3]))
    child = np.concatenate((parent1, parent2, parent3))
    return grandparent1, parent1, grandparent2, parent2, parent3, child


def test_get_overrides_for_assignment_when_nothing_is_overridable(assignment, parent_and_child):
    parent, child = parent_and_child
    parent.allow_overriding = False

    with raises(CannotAssignException) as exc_info:
        get_overrides_for_assignment(child, assignment)
    assert exc_info.value.assignment is assignment
    assert exc_info.value.quib is child


def test_get_overrides_for_assignment_when_reverse_assignment_not_implemented(assignment):
    parent = iquib(1)
    child = DefaultFunctionQuib.create(lambda x: x, (parent,))
    assignment = Assignment(5, [...])

    with raises(CannotAssignException) as exc_info:
        get_overrides_for_assignment(child, assignment)
    assert exc_info.value.assignment is assignment
    assert exc_info.value.quib is child


def test_get_overrides_for_assignment_when_diverged_reverse_assign_has_only_one_overridable_child(assignment,
                                                                                                  diverged_quib_graph):
    grandparent1, parent1, grandparent2, parent2, parent3, child = diverged_quib_graph
    grandparent2.allow_overriding = False

    with raises(CannotAssignException) as exc_info:
        get_overrides_for_assignment(child, assignment)
    assert exc_info.value.assignment is assignment
    assert exc_info.value.quib is child


def test_get_overrides_for_assignment_on_iquib(assignment):
    quib = iquib(1)

    overrides = get_overrides_for_assignment(quib, assignment)

    assert overrides == [QuibWithAssignment(quib, assignment)]


def test_get_overrides_for_assignment_on_quib_without_overridable_parents(assignment, parent_and_child):
    parent, child = parent_and_child
    parent.allow_overriding = False
    child.allow_overriding = True

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [QuibWithAssignment(child, assignment)]


def test_get_overrides_for_assignment_on_non_overridable_quib_with_overridable_parent(assignment, parent_and_child):
    parent, child = parent_and_child

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [QuibWithAssignment(parent, Assignment(4, [...]))]


def test_get_overrides_for_assignment_with_choice_to_override_child(assignment, choose_override_dialog_mock,
                                                                    parent_and_child):
    parent, child = parent_and_child
    child.allow_overriding = True
    chosen_override = QuibWithAssignment(child, assignment)
    choose_override_dialog_mock.side_effect.add_choices(OverrideChoice(OverrideChoiceType.OVERRIDE, chosen_override))

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [chosen_override]


def test_get_overrides_for_assignment_with_choice_to_override_parent(assignment, choose_override_dialog_mock,
                                                                     parent_and_child):
    parent, child = parent_and_child
    child.allow_overriding = True
    chosen_override = QuibWithAssignment(parent, Assignment(4, [...]))
    choose_override_dialog_mock.side_effect.add_choices(OverrideChoice(OverrideChoiceType.OVERRIDE, chosen_override))

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == [chosen_override]


def test_override_choice_when_cancelled(assignment, choose_override_dialog_mock, parent_and_child):
    parent, child = parent_and_child
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(OverrideChoice(OverrideChoiceType.CANCEL))

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == []


def test_override_choice_when_diverged_parent_is_cancelled(diverged_quib_graph, assignment,
                                                           choose_override_dialog_mock):
    grandparent1, parent1, grandparent2, parent2, parent3, child = diverged_quib_graph
    parent1.allow_overriding = True
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(OverrideChoice(OverrideChoiceType.DIVERGE),
                                                        OverrideChoice(OverrideChoiceType.CANCEL))

    overrides = get_overrides_for_assignment(child, assignment)

    assert overrides == []

# test caching, test diverged trees
