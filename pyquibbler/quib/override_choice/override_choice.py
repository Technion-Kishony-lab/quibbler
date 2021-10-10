from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional, Dict, Any

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import QuibWithAssignment, reverse_function_quib, CannotReverseException, Assignment

from .override_dialog import OverrideChoiceType, OverrideChoice, choose_override_dialog

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib, Quib


@dataclass
class CannotAssignException(PyQuibblerException):
    quib: Quib
    assignment: Assignment

    def __str__(self):
        return f'Cannot perform {self.assignment} on {self.quib}, because it cannot ' \
               f'be overridden and we could not find an overridable parnet quib to reverse assign into.'


class ChoiceCache:
    """
    Implements caching for user override choices.
    A choice can be reused in the context of a new assignment,
    if the reversed quib (the quib that was originally assigned to) is the same, and the options are the same.
    The override options for a reversed quib might change because when different indices are assigned to, the
    reversal tree might change (for example if one of the quib's parents is concat).
    """

    def __init__(self):
        self._map: Dict[Any, OverrideChoice] = {}

    def _get_key(self, reversed_quib: Quib, options_tree: OverrideOptionsTree):
        """
        Returns a key for cache lookup.
        """
        return (reversed_quib,
                frozenset({id(option.quib) for option in options_tree.options}),
                options_tree.can_diverge)

    def store(self, choice: OverrideChoice, reversed_quib: Quib, options_tree: OverrideOptionsTree):
        """
        Store the given user choice according to the reversed quib and the options.
        """
        self._map[self._get_key(reversed_quib, options_tree)] = choice

    def load(self, reversed_quib: Quib, options_tree: OverrideOptionsTree) -> Optional[OverrideChoice]:
        """
        Try to find a cached choice for the given reversed quib and override options.
        """
        return self._map.get(self._get_key(reversed_quib, options_tree))


@dataclass
class OverrideOptionsTree:
    """
    When assigning to a quib, we can climb up the dependency tree using reverse assignments
    and collect potential overrides, which the user can choose from.
    But if one of the quibs has multiple parents that can be reverse assigned into, then we get new sets of overrides.
    In each of those sets, the user will have to choose a specific override, but none of those overrides are even
    an option if the user chooses to apply an override to a quib before the quib with multiple parents.
    For this reason the override options for an assignment are structured like a tree.
    Each node has the following members:

    - reversed_quib: the quib the original assignment was made to
    - options:       a list of overrides that can each be performed to satisfy the original assignment
    - diverged_quib: a quib which translates a reverse assign into multiple assignments which can all lead to overrides
    - children:      subtrees of override options of which the reversed quib is the current diverged_quib
    """
    _CHOICE_CACHE = ChoiceCache()

    reversed_quib: FunctionQuib
    options: List[QuibWithAssignment]
    diverged_quib: Optional[FunctionQuib]
    children: List[OverrideOptionsTree]

    def __post_init__(self):
        if self.children:
            assert self.diverged_quib is not None
        else:
            assert self.diverged_quib is None

    @property
    def can_diverge(self):
        return len(self.children) > 0

    def __bool__(self):
        return len(self.options) > 0 or self.can_diverge

    def _try_load_choice(self) -> Optional[OverrideChoice]:
        choice = self._CHOICE_CACHE.load(self.reversed_quib, self)
        if choice is not None and choice.choice_type is OverrideChoiceType.OVERRIDE:
            chosen_quib = choice.chosen_override.quib
            option = next(option for option in self.options if option.quib is chosen_quib)
            choice = OverrideChoice(choice.choice_type, option)
        return choice

    def _store_choice(self, choice: OverrideChoice):
        self._CHOICE_CACHE.store(choice, self.reversed_quib, self)

    def get_override_choice(self) -> OverrideChoice:
        if len(self.options) == 1 and not self.can_diverge:
            return OverrideChoice(OverrideChoiceType.OVERRIDE, self.options[0])
        choice = self._try_load_choice()
        if choice is None:
            choice = choose_override_dialog(self.options, self.can_diverge)
            if choice.choice_type is not OverrideChoiceType.CANCEL:
                self._store_choice(choice)
        return choice

    def choose_overrides_from_diverged_reverse_assignment(self) -> List[QuibWithAssignment]:
        chosen_overrides = []
        for child in self.children:
            new_overrides = child.choose_overrides()
            if not new_overrides:
                # One of the diverged branches was cancelled, so we cancel the whole assignment
                return []
            chosen_overrides.extend(new_overrides)
        return chosen_overrides

    def choose_overrides(self) -> List[QuibWithAssignment]:
        choice_type = OverrideChoiceType.DIVERGE
        if self.options:
            choice = self.get_override_choice()
            choice_type = choice.choice_type
            if choice_type is OverrideChoiceType.CANCEL:
                return []
            elif choice_type is OverrideChoiceType.OVERRIDE:
                # if override_choice is OverrideChoiceType.OVERRIDE, metadata is the choice index
                return [choice.chosen_override]

        assert self.can_diverge
        assert choice_type is OverrideChoiceType.DIVERGE
        return self.choose_overrides_from_diverged_reverse_assignment()

    @classmethod
    def _get_next_reversals(cls, reversal: QuibWithAssignment):
        from pyquibbler.quib import FunctionQuib
        if isinstance(reversal.quib, FunctionQuib):
            try:
                return reverse_function_quib(reversal.quib, reversal.assignment)
            except CannotReverseException:
                pass
        return []

    @classmethod
    def _get_children_from_diverged_reversals(cls, reversals: List[QuibWithAssignment]):
        children = []
        for reversal in reversals:
            child = cls.from_reversal(reversal)
            if not child:
                # If one of the diverged options does not allow overriding,
                # then we can't reverse assign through the diverger, because
                # only one of the reverse assignment threads will be able to end with an override.
                return []
            children.append(child)
        return children

    @classmethod
    def from_reversal(cls, quib_with_assignment: QuibWithAssignment) -> OverrideOptionsTree:
        options = []
        reversals = [quib_with_assignment]
        last_reversal = None
        while len(reversals) == 1:
            reversal = reversals[0]
            if reversal.quib.allow_overriding:
                options.append(reversal)
            reversals = cls._get_next_reversals(reversal)
            if reversals:
                last_reversal = reversal

        children = cls._get_children_from_diverged_reversals(reversals)
        diverged_quib = None if not children else last_reversal.quib
        return OverrideOptionsTree(quib_with_assignment.quib, options, diverged_quib, children)


def get_overrides_for_assignment(quib: Quib, assignment: Assignment) -> List[QuibWithAssignment]:
    """
    Every assignment to a quib is translated at the end to a list of overrides to quibs in the graph.
    This function determines those overrides and returns them.
    When the assignment cannot be translated, CannotAssignException is raised.
    The returned override list might be empty if the user has chosen to cancel the assignment.
    """
    options_tree = OverrideOptionsTree.from_reversal(QuibWithAssignment(quib, assignment))
    if not options_tree:
        raise CannotAssignException(quib, assignment)
    return options_tree.choose_overrides()


def get_overrides_for_assignment_group(quibs_with_assignments: List[QuibWithAssignment]):
    """
    Get all overrides for a group of assignments, filter them to leave out contradictory assignments
    (assignments that cause overrides in the same quibs) and return the remaining overrides.
    """
    all_overridden_quibs = set()
    all_overrides = []
    for quib_with_assignment in quibs_with_assignments:
        try:
            current_overrides = get_overrides_for_assignment(quib_with_assignment.quib, quib_with_assignment.assignment)
        except CannotAssignException:
            continue
        current_overridden_quibs = set(override.quib for override in current_overrides)
        if not current_overridden_quibs.intersection(all_overridden_quibs):
            all_overridden_quibs.update(current_overridden_quibs)
            all_overrides.extend(current_overrides)
    return all_overrides
