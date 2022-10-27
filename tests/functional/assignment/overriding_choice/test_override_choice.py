import numpy as np
from typing import List, Tuple, Union
from unittest.mock import Mock
from pytest import raises, fixture, mark

from pyquibbler import iquib, q, Assignment, default
from pyquibbler.assignment import AssignmentToQuib
from pyquibbler.assignment import get_override_group_for_quib_change, OverrideChoice, OverrideGroup
from pyquibbler.assignment import OverrideOptionsTree, \
    CannotChangeQuibAtPathException
from pyquibbler.assignment import OverrideChoiceType, \
    AssignmentCancelledByUserException
from pyquibbler.assignment import override_choice as override_choice_module
from pyquibbler.path import PathComponent
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.get_value_context_manager import get_value_context
from pyquibbler.quib.specialized_functions.proxy import create_proxy


def get_overrides_for_assignment(quib, assignment: Assignment):
    if assignment.value is default:
        return get_override_group_for_quib_change(AssignmentToQuib.create_default(quib, assignment.path))
    else:
        return get_override_group_for_quib_change(AssignmentToQuib(quib, assignment))


class ChooseOverrideDialogMockSideEffect:
    def __init__(self):
        self.choices = []

    def add_choices(self, *choices: Tuple[Union[OverrideChoice, Exception], List[AssignmentToQuib], bool]):
        self.choices = [*self.choices, *choices]

    def __call__(self, options: List[AssignmentToQuib], can_diverge: bool):
        assert self.choices, 'The dialog mock was called more times than expected'
        (choice, expected_options, excpected_can_diverge) = self.choices.pop(0)
        assert expected_options == options
        assert excpected_can_diverge == can_diverge
        assert options, 'There is no reason to open a dialog without options'
        if isinstance(choice, Exception):
            raise choice
        if choice.choice_type is OverrideChoiceType.OVERRIDE:
            assert isinstance(choice.chosen_index, int)
            assert choice.chosen_index < len(options), \
                f'Chose option {choice.chosen_index} which is out of bounds for {options}'
        elif choice.choice_type is OverrideChoiceType.DIVERGE:
            assert can_diverge, 'Chose to diverge but it is not an option'
        return choice

    def assert_all_choices_made(self):
        assert not self.choices, f'Not all choices were made, left with: {self.choices}'


@fixture
def assignment():
    return Assignment(5, [])


@fixture
def default_assignment():
    return Assignment(default, [])


@fixture
def assignment_to_multiple():
    return Assignment(value=[3, 4], path=[PathComponent((None, None, None))])


@fixture(autouse=True)
def clear_choice_cache():
    OverrideOptionsTree._CHOICE_CACHE.clear()


@fixture
def choose_override_dialog_mock():
    side_effect = ChooseOverrideDialogMockSideEffect()
    yield Mock(side_effect=side_effect)
    side_effect.assert_all_choices_made()


@fixture(autouse=True)
def override_choice_dialog(monkeypatch, choose_override_dialog_mock):
    """
    This fixture is autouse, because if a dialog is erroneously invoked from a test,
    we want it to fail rather then open an actual dialog and block.
    """
    overridden_name = 'choose_override_dialog'
    assert hasattr(override_choice_module, overridden_name), \
        f'This fixture assumes that the {override_choice_module.__name__} module imports {overridden_name}, ' \
        f'as the fixture tries to replace the function with a mock.'
    monkeypatch.setattr(override_choice_module, overridden_name, choose_override_dialog_mock)


@fixture
def parent_and_child(assignment):
    add = 1
    parent = iquib(1)
    child: Quib = parent + add
    child_override = OverrideGroup([AssignmentToQuib(child, assignment)])

    parent_override = OverrideGroup([AssignmentToQuib(parent, Assignment(assignment.value - add, [])),
                                     AssignmentToQuib.create_default(child, [])])
    return parent, child, parent_override, child_override


@fixture
def diverged_quib_graph(assignment):
    grandparent1 = iquib(np.array([1]))
    parent1: Quib = grandparent1 * 1.
    grandparent2 = iquib(np.array([2]))
    parent2: Quib = grandparent2 * 1.
    child: Quib = np.concatenate((parent1, parent2))
    parent1_override = None  # Override(parent1, Assignment(np.array([assignment.value]), [(np.array([0]),)]))
    return grandparent1, parent1, grandparent2, parent2, child, parent1_override


def test_get_overrides_for_assignment_when_nothing_is_overridable(assignment, parent_and_child):
    parent, child, parent_override, child_override = parent_and_child
    parent.allow_overriding = False

    assignment = AssignmentToQuib(child, assignment)
    with raises(CannotChangeQuibAtPathException, match='.*') as exc_info:
        get_override_group_for_quib_change(assignment)
    assert exc_info.value.quib_change is assignment


def test_get_overrides_for_assignment_when_inverse_assignment_not_implemented(assignment):
    parent = iquib(1)
    child = create_quib(func=lambda x: x, args=(parent,))
    assignment = AssignmentToQuib(child, assignment)

    with raises(CannotChangeQuibAtPathException, match='.*') as exc_info:
        get_override_group_for_quib_change(assignment)
    assert exc_info.value.quib_change is assignment


def test_get_overrides_for_assignment_when_diverged_inverse_assign_has_only_one_overridable_child(assignment_to_multiple,
                                                                                                  diverged_quib_graph):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    grandparent2.allow_overriding = False

    assignment = AssignmentToQuib(child, assignment_to_multiple)
    with raises(CannotChangeQuibAtPathException, match='.*') as exc_info:
        get_override_group_for_quib_change(assignment)
    assert exc_info.value.quib_change is assignment


def test_get_overrides_for_assignment_on_iquib(assignment):
    quib = iquib(1)

    override_group = get_overrides_for_assignment(quib, assignment)

    assert override_group == OverrideGroup([AssignmentToQuib(quib, assignment)])


def test_get_overrides_for_default_assignment_on_iquib(default_assignment):
    quib = iquib(1)

    override_group = get_overrides_for_assignment(quib, default_assignment)

    assert override_group == OverrideGroup([AssignmentToQuib(quib, Assignment.create_default(default_assignment.path))])


def test_get_overrides_for_assignment_on_quib_without_overridable_parents(assignment, parent_and_child):
    parent, child, parent_override, child_override = parent_and_child
    parent.allow_overriding = False
    child.allow_overriding = True

    override_group = get_overrides_for_assignment(child, assignment)

    assert override_group == child_override


def test_get_overrides_for_assignment_on_non_overridable_quib_with_overridable_parent(assignment, parent_and_child):
    parent, child, parent_override, child_override = parent_and_child

    override_group = get_overrides_for_assignment(child, assignment)

    assert override_group == parent_override


def test_get_overrides_for_default_assignment_on_non_overridable_quib_with_overridable_parent(default_assignment, parent_and_child):
    parent, child, parent_override, child_override = parent_and_child

    override_group = get_overrides_for_assignment(child, default_assignment)

    assert override_group == OverrideGroup([AssignmentToQuib.create_default(parent, default_assignment.path),
                                            AssignmentToQuib.create_default(child, default_assignment.path)])


@mark.parametrize('parent_chosen', [True, False])
def test_get_overrides_for_assignment_with_choice_to_override_child(assignment, choose_override_dialog_mock,
                                                                    parent_and_child, parent_chosen):
    parent, child, parent_override, child_override = parent_and_child
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (OverrideChoice(OverrideChoiceType.OVERRIDE, 1 if parent_chosen else 0),
         [child, parent],
         False)
    )

    override_group = get_overrides_for_assignment(child, assignment)

    assert override_group == parent_override if parent_chosen else child_override


def test_override_choice_when_cancelled(assignment, choose_override_dialog_mock, parent_and_child):
    parent, child, parent_override, child_override = parent_and_child
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (AssignmentCancelledByUserException(),
         [child, parent],
         False)
    )

    with raises(AssignmentCancelledByUserException, match='.*'):
        get_overrides_for_assignment(child, assignment)


def test_override_choice_when_diverged_parent_is_cancelled(diverged_quib_graph, assignment_to_multiple,
                                                           choose_override_dialog_mock):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    parent1.allow_overriding = True
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (OverrideChoice(OverrideChoiceType.DIVERGE), [child], True),
        (AssignmentCancelledByUserException(), [parent1, grandparent1], False)
    )

    with raises(AssignmentCancelledByUserException, match='.*'):
        get_overrides_for_assignment(child, assignment_to_multiple)


def test_override_choice_when_diverged_and_all_diverged_inversions_are_overridden(diverged_quib_graph, assignment,
                                                                                  choose_override_dialog_mock):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph

    override_group = get_overrides_for_assignment(child, Assignment(value=[3, 4],
                                                                    path=[PathComponent((None, None, None))]))

    assert len([o for o in override_group.quib_changes if not o.assignment.is_default()]) == 2
    assert len([o for o in override_group.quib_changes if o.assignment.is_default()]) == 3


def create_proxy_created_in_context(quib):
    proxy = create_proxy(quib)
    proxy.handler.created_in_get_value_context = True
    return proxy


@mark.parametrize('parent_chosen', [True, False], ids=['parent_chosen', 'child_chosen'])
@mark.parametrize('proxy_first_time', [True, False], ids=['proxy_first_time', 'not_proxy_first_time'])
@mark.parametrize('proxy_second_time', [True, False], ids=['proxy_second_time', 'not_proxy_second_time'])
def test_get_overrides_for_assignment_caches_override_choice(assignment, parent_and_child,
                                                             choose_override_dialog_mock, parent_chosen,
                                                             proxy_first_time, proxy_second_time):
    parent, child, parent_override, child_override = parent_and_child
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (OverrideChoice(OverrideChoiceType.OVERRIDE, 1 if parent_chosen else 0),
         [child, parent],
         False)
    )

    override_group = get_overrides_for_assignment(create_proxy_created_in_context(child) if proxy_first_time else child, assignment)
    # If this invokes a dialog, the dialog mock will fail the test
    second_override_group = get_overrides_for_assignment(create_proxy_created_in_context(child) if proxy_second_time else child,
                                                         Assignment(assignment.value + 1, assignment.path))

    assert override_group == (parent_override if parent_chosen else child_override)
    assert second_override_group != override_group


def test_get_overrides_for_assignment_caches_diverged_choices(diverged_quib_graph, assignment_to_multiple,
                                                              choose_override_dialog_mock):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    parent1.allow_overriding = True
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (OverrideChoice(OverrideChoiceType.DIVERGE), [child], True),
        (OverrideChoice(OverrideChoiceType.OVERRIDE, 1), [parent1, grandparent1], False),
    )

    override_group = get_overrides_for_assignment(child, assignment_to_multiple)
    # If this invokes a dialog, the dialog mock will fail the test

    second_override_group = get_overrides_for_assignment(child, Assignment([666, 999], assignment_to_multiple.path))

    assert override_group != second_override_group


def test_get_overrides_for_assignment_doesnt_cache_cancel(assignment, parent_and_child, choose_override_dialog_mock):
    parent, child, parent_override, child_override = parent_and_child
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (AssignmentCancelledByUserException(), [child, parent], False),
        (AssignmentCancelledByUserException(), [child, parent], False)
    )

    with raises(AssignmentCancelledByUserException, match='.*'):
        get_overrides_for_assignment(child, assignment)
    # If this doesn't invoke a dialog, the dialog mock will fail the test
    with raises(AssignmentCancelledByUserException, match='.*'):
        get_overrides_for_assignment(child, Assignment(assignment.value + 1, assignment.path))


def test_get_overrides_for_assignment_does_not_use_cache_when_diverge_changes(diverged_quib_graph,
                                                                              assignment_to_multiple,
                                                                              choose_override_dialog_mock):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    parent1.allow_overriding = True
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (OverrideChoice(OverrideChoiceType.DIVERGE), [child], True),
        (OverrideChoice(OverrideChoiceType.OVERRIDE, 1), [parent1, grandparent1], False),
    )

    get_overrides_for_assignment(child, assignment_to_multiple)
    # Now we can't diverge
    grandparent2.allow_overriding = False

    assignment2 = Assignment([999, 444], assignment_to_multiple.path)
    override_group = get_overrides_for_assignment(child, assignment2)

    assert override_group == OverrideGroup([AssignmentToQuib(child, assignment2)])


def test_get_overrides_for_assignment_does_not_use_cache_when_options_change(assignment, parent_and_child,
                                                                             choose_override_dialog_mock):
    parent, child, parent_override, child_override = parent_and_child
    child.allow_overriding = True
    choose_override_dialog_mock.side_effect.add_choices(
        (OverrideChoice(OverrideChoiceType.OVERRIDE, 0), [child, parent], False)
    )

    get_overrides_for_assignment(child, assignment)
    parent.allow_overriding = False

    assignment2 = Assignment(assignment.value + 1, assignment.path)
    second_override_group = get_overrides_for_assignment(child, assignment2)

    assert second_override_group == OverrideGroup([AssignmentToQuib(child, assignment2)])


def test_get_overrides_for_assignment_when_can_assign_to_self(diverged_quib_graph, assignment_to_multiple):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    parent1.allow_overriding = True
    child.allow_overriding = True
    child.assigned_quibs = [child]
    assignment = AssignmentToQuib(child, assignment_to_multiple)
    override_group = get_override_group_for_quib_change(assignment)

    assert override_group.quib_changes == [assignment]


def test_get_overrides_for_assignment_when_can_assign_to_parents(diverged_quib_graph, assignment_to_multiple):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    parent1.allow_overriding = True
    parent2.allow_overriding = True
    child.assigned_quibs = [parent1, parent2]
    assignment = AssignmentToQuib(child, assignment_to_multiple)
    override_group = get_override_group_for_quib_change(assignment)

    assert len(override_group.quib_changes) == 3  # Two overrides and one override removal


def test_get_overrides_for_assignment_with_differed_assigned_quibs(diverged_quib_graph, assignment_to_multiple):
    grandparent1, parent1, grandparent2, parent2, child, parent1_override = diverged_quib_graph
    parent1.allow_overriding = True
    parent2.allow_overriding = True
    grandparent1.allow_overriding = True
    grandparent2.allow_overriding = True
    parent1.assigned_quibs = 'self'
    parent2.assigned_quibs = grandparent2
    child.assigned_quibs = None  # assigned quibs will be chosen based on assigned_quibs of upstream quibs
    assignment = AssignmentToQuib(child, assignment_to_multiple)
    override_group = get_override_group_for_quib_change(assignment)

    assert len(override_group.quib_changes) == 4  # Two overrides and two override removal


def test_raises_cannot_change_when_context_quib_cannot_be_inverted():
    with get_value_context():
        # A function we don't know to invert
        child = q(lambda x: x, 10)
    with raises(CannotChangeQuibAtPathException, match='.*'):
        get_override_group_for_quib_change(AssignmentToQuib(child, Assignment(1, [])))


def test_get_override_group_on_context_quibs():
    non_context_parent = iquib(0)
    with get_value_context(pass_quibs=True):
        context_parent = iquib(1)
        child = non_context_parent + context_parent
        child.allow_overriding = True

    override_group = get_override_group_for_quib_change(AssignmentToQuib(child, Assignment(2, [])))
    assert override_group.quib_changes == [AssignmentToQuib(non_context_parent, Assignment(1, []))]
