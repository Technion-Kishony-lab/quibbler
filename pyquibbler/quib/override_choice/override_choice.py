from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.assignment import QuibWithAssignment, CannotReverseException, \
    Assignment

from .override_dialog import OverrideChoiceType, OverrideChoice, choose_override_dialog
from .types import OverrideRemoval, OverrideGroup, OverrideWithOverrideRemovals
from .choice_cache import ChoiceCache

if TYPE_CHECKING:
    from pyquibbler.quib import Quib, FunctionQuib


@dataclass
class AssignmentNotPossibleException(PyQuibblerException):
    quib: Quib
    assignment: Assignment

    def __str__(self):
        return f'Cannot perform {self.assignment} on {self.quib}, because it cannot ' \
               f'be overridden and we could not find an overridable parent quib to inverse assign into.\n' \
               f'Don\'t forget that non-input quibs are not overridable by default.\n' \
               f'To allow overriding {self.quib}, try using "{self.quib}.allow_overriding = True"'


@dataclass
class OverrideOptionsTree:
    """
    When assigning to a quib, we can climb up the dependency tree using inverse assignments
    and collect potential overrides, which the user can choose from.
    But if one of the quibs has multiple parents that can be inverse assigned into, then we get new sets of overrides.
    In each of those sets, the user will have to choose a specific override, but none of those overrides are even
    an option if the user chooses to apply an override to a quib before the quib with multiple parents.
    For this reason the override options for an assignment are structured like a tree.
    Note that the children in this tree are parents in the quib graph.
    Each node in the tree has the following members:

    - inversed_quib:     the quib the original assignment was made to
    - options:           a list of overrides that can each be performed to satisfy the original assignment
    - diverged_quib:     a quib which translates a inverse assign into multiple
                         assignments which can all lead to overrides
    - children:          subtrees of override options of which the inversed quib is the current diverged_quib
    - override_removals: all the override removals that will have to be applied if we
                         diverge and use children overrides
    """
    _CHOICE_CACHE = ChoiceCache()

    inversed_quib: FunctionQuib
    options: List[OverrideWithOverrideRemovals]
    diverged_quib: Optional[FunctionQuib]
    children: List[OverrideOptionsTree]
    override_removals: List[OverrideRemoval]

    def __post_init__(self):
        if self.children:
            assert self.diverged_quib is not None
        else:
            assert self.diverged_quib is None

    @property
    def can_diverge(self):
        """
        Return True if the original assignment can be translated into
        multiple assignment into ancestor quibs, and False otherwise.
        Note that self.children will be empty if any of these assignments cannot be translated into an override.
        """
        return len(self.children) > 0

    def __bool__(self):
        """
        Return True if the original assignment can be translated into an override and False otherwise.
        """
        return len(self.options) > 0 or self.can_diverge

    def _try_load_choice(self) -> Optional[OverrideChoice]:
        """
        If a choice fitting the current options has been cached, return it. Otherwise return None.
        """
        return self._CHOICE_CACHE.load(self.inversed_quib, self)

    def _store_choice(self, choice: OverrideChoice):
        """
        Store a user override choice in the cache for future use.
        """
        self._CHOICE_CACHE.store(choice, self.inversed_quib, self)

    def get_override_choice(self) -> OverrideChoice:
        """
        Choose an override from the options or choose to diverge.
        If there is only one option and can't diverge, return it.
        If there are no options and can diverge, diverge.
        Otherwise, prompt the user to choose.
        """
        if len(self.options) == 1 and not self.can_diverge:
            return OverrideChoice(OverrideChoiceType.OVERRIDE, 0)
        choice = self._try_load_choice()
        if choice is None:
            choice = choose_override_dialog([override.override.quib for override in self.options], self.can_diverge)
            self._store_choice(choice)
        return choice

    def choose_overrides_from_diverged_inverse_assignment(self) -> OverrideGroup:
        """
        If we have chosen to diverge our overrides, we must choose an override for each diverged assignment.
        If one of the diverged assignments is canceled, the whole operation is cancelled to we don't override
        partially.
        """
        override_group = OverrideGroup()
        for child in self.children:
            child_override_group = child.choose_overrides()
            assert child_override_group, \
                'One child returned an empty option tree, cannot build a complete override choice'
            override_group.extend(child_override_group)
        return override_group

    def choose_overrides(self) -> OverrideGroup:
        """
        Choose and return the overrides for this node.
        """
        choice_type = OverrideChoiceType.DIVERGE
        if self.options:
            choice = self.get_override_choice()
            choice_type = choice.choice_type
            if choice_type is OverrideChoiceType.OVERRIDE:
                # if override_choice is OverrideChoiceType.OVERRIDE, metadata is the choice index
                chosen_override = self.options[choice.chosen_index]
                return OverrideGroup([chosen_override.override], chosen_override.override_removals)

        assert self.can_diverge
        assert choice_type is OverrideChoiceType.DIVERGE
        override_group = self.choose_overrides_from_diverged_inverse_assignment()
        override_group.extend(self.override_removals)
        return override_group

    @classmethod
    def _inverse_assignment(cls, quib_with_assignment: QuibWithAssignment) -> List[QuibWithAssignment]:
        """
        Try to inverse the given assignment and return the resulting assignments.
        Return an empty list if cannot inverse.
        """
        from pyquibbler.quib import FunctionQuib
        if isinstance(quib_with_assignment.quib, FunctionQuib):
            try:
                return quib_with_assignment.quib.get_inversions_for_assignment(quib_with_assignment.assignment)
            except CannotReverseException:
                pass
        return []

    @classmethod
    def _get_children_from_diverged_inversions(cls, inversions: List[QuibWithAssignment]):
        """
        For each diverged inversion, create a new OverrideOptionsTree instance, and return a list of all instances.
        If any inversion cannot be translated into an override, return an empty list.
        """
        children = []
        for inversion in inversions:
            child = cls.from_assignment(inversion)
            if not child:
                # If one of the diverged options does not allow overriding,
                # then we can't inverse assign through the diverger, because
                # only one of the inverse assignment threads will be able to end with an override.
                return []
            children.append(child)
        return children

    @classmethod
    def from_assignment(cls, quib_with_assignment: QuibWithAssignment) -> OverrideOptionsTree:
        """
        Build an OverrideOptionsTree representing all the override options for the given assignment.
        """
        options: List[OverrideWithOverrideRemovals] = []
        inversions = [quib_with_assignment]
        override_removals = []
        last_inversion = None
        while len(inversions) == 1:
            inversion = inversions[0]
            if inversion.quib.allow_overriding:
                options.append(OverrideWithOverrideRemovals(inversion, override_removals[:]))
            override_removals.append(OverrideRemoval.from_inversion(inversion))
            inversions = cls._inverse_assignment(inversion)
            if inversions:
                last_inversion = inversion

        children = cls._get_children_from_diverged_inversions(inversions)
        diverged_quib = None if not children else last_inversion.quib
        return OverrideOptionsTree(quib_with_assignment.quib, options, diverged_quib, children, override_removals)


def get_overrides_for_assignment(quib: Quib, assignment: Assignment) -> OverrideGroup:
    """
    Every assignment to a quib is translated at the end to a list of overrides to quibs in the graph.
    This function determines those overrides and returns them.
    When the assignment cannot be translated, AssignmentNotPossibleException is raised.
    Might raise AssignmentCancelledByUserException if a user cancels an override choice dialog.
    """
    options_tree = OverrideOptionsTree.from_assignment(QuibWithAssignment(quib, assignment))
    if not options_tree:
        raise AssignmentNotPossibleException(quib, assignment)
    return options_tree.choose_overrides()


def get_overrides_for_assignment_group(quibs_with_assignments: List[QuibWithAssignment]) -> OverrideGroup:
    """
    Get all overrides for a group of assignments, filter them to leave out contradictory assignments
    (assignments that cause overrides in the same quibs) and return the remaining overrides.
    """
    all_overridden_quibs = set()
    result = OverrideGroup()
    for quib_with_assignment in quibs_with_assignments:
        try:
            override_group = get_overrides_for_assignment(quib_with_assignment.quib, quib_with_assignment.assignment)
        except AssignmentNotPossibleException:
            continue
        current_overridden_quibs = set(override.quib for override in override_group.overrides)
        if not current_overridden_quibs.intersection(all_overridden_quibs):
            all_overridden_quibs.update(current_overridden_quibs)
            result.extend(override_group)
    return result
