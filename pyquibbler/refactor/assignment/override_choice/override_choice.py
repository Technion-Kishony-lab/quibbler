from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional, Dict, ClassVar, Union

from pyquibbler.refactor.exceptions import PyQuibblerException
from pyquibbler.refactor.assignment import AssignmentToQuib, QuibChange

from .choice_context import ChoiceContext
from .override_dialog import OverrideChoiceType, OverrideChoice, choose_override_dialog
from .types import OverrideRemoval, OverrideGroup, QuibChangeWithOverrideRemovals
from pyquibbler.refactor.env import ASSIGNMENT_RESTRICTIONS

if TYPE_CHECKING:
    from pyquibbler.refactor.quib import Quib


@dataclass
class CannotChangeQuibAtPathException(PyQuibblerException):
    quib_change: QuibChange

    def __str__(self):
        return f'Cannot perform {self.quib_change} on {self.quib_change.quib}, because it cannot ' \
               f'be overridden and an overridable parent quib to inverse assign into was not found.\n' \
               f'Note that functional quibs are not overridable by default.\n' \
               f'To allow overriding, try using "{self.quib_change.quib}.set_allow_overriding(True)"'


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
    _CHOICE_CACHE: ClassVar[Dict[ChoiceContext, OverrideChoice]] = {}

    inversed_quib: Quib
    options: List[QuibChangeWithOverrideRemovals]
    diverged_quib: Optional[Quib]
    children: List[OverrideOptionsTree]
    override_removals: List[OverrideRemoval]

    def __post_init__(self):
        assert (len(self.children) > 0) is (self.diverged_quib is not None)

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

    @property
    def choice_context(self):
        return ChoiceContext(tuple(option.quib for option in self.options), self.can_diverge)

    def get_override_choice(self) -> OverrideChoice:
        """
        Choose an override from the options or choose to diverge.
        If there is only one option and can't diverge, return it.
        If there are no options and can diverge, diverge.
        Otherwise, prompt the user to choose.
        """
        if len(self.options) == 1 and not self.can_diverge:
            return OverrideChoice(OverrideChoiceType.OVERRIDE, 0)
        choice = self.inversed_quib.try_load_override_choice(self.choice_context)
        if choice is None:
            choice = choose_override_dialog([override.quib for override in self.options], self.can_diverge)
            self.inversed_quib.store_override_choice(self.choice_context, choice)
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
                return OverrideGroup([chosen_override.change, *chosen_override.override_removals])

        assert self.can_diverge
        assert choice_type is OverrideChoiceType.DIVERGE
        override_group = self.choose_overrides_from_diverged_inverse_assignment()
        override_group.extend(self.override_removals)
        return override_group

    @classmethod
    def _get_children_from_diverged_inversions(cls, inversions: List[AssignmentToQuib], top_quib: Quib):
        """
        For each diverged inversion, create a new OverrideOptionsTree instance, and return a list of all instances.
        If any inversion cannot be translated into an override, return an empty list.
        """
        children = []
        for inversion in inversions:
            child = cls.from_quib_change(inversion, top_quib)
            if not child:
                # If one of the diverged options does not allow function_definitions,
                # then we can't inverse assign through the diverger, because
                # only one of the inverse assignment threads will be able to end with an override.
                return []
            children.append(child)
        return children

    @classmethod
    def _convert_quib_change_to_change_in_context_quib(cls, quib_change: Union[AssignmentToQuib, OverrideRemoval]):
        """
        Invert the given change until we get a change to a non-context quib.
        This is used to treat an assignment to a context-quib as an assignment to a non-context quib when building
        an override choice tree.
        Solves a few problems when a user function is run in context of a quib, such as when vectorize is used with
        pass_quibs=True:

        - We don't want to allow overrides to quibs created in a context (the overrides will disappear in the next
          evaluation
        - We want to cache level choices made on an assignment to a quib which was created in a context
        - Overrides and override removals to quibs in a context will cause the context quibs to be redrawn, which is
          incorrect behavior as the context quib is supposed to do the redrawing
        """
        inversions = [quib_change]
        while True:
            if not inversions:
                raise CannotChangeQuibAtPathException(quib_change)
            non_context_inversions = [inversion for inversion in inversions
                                      if not inversion.quib.created_in_get_value_context]
            assert len(non_context_inversions) < 2
            if non_context_inversions:
                return non_context_inversions[0]
            inversions = [new_inversion for inversion in inversions
                          for new_inversion in inversion.get_inversions(True)]

    @classmethod
    def from_quib_change(cls, quib_change: Union[AssignmentToQuib, OverrideRemoval],
                         top_quib: Optional[Quib] = None) -> OverrideOptionsTree:
        """
        Build an OverrideOptionsTree representing all the override options for the given assignment.
        """
        quib_change = cls._convert_quib_change_to_change_in_context_quib(quib_change)
        if top_quib is None:
            top_quib = quib_change.quib
        options: List[QuibChangeWithOverrideRemovals] = []
        inversions = [quib_change]
        override_removals = []
        last_inversion = None
        while len(inversions) == 1:
            inversion = inversions[0]
            if inversion.quib.allow_overriding and top_quib.allows_assignment_to(inversion.quib):
                override = inversion.to_override() if isinstance(inversion, AssignmentToQuib) else inversion
                options.append(QuibChangeWithOverrideRemovals(override, override_removals[:]))
            override_removals.append(OverrideRemoval.from_quib_change(inversion))
            inversions = inversion.get_inversions(True)
            if inversions:
                last_inversion = inversion

        children = cls._get_children_from_diverged_inversions(inversions, top_quib)
        diverged_quib = None if not children else last_inversion.quib
        return OverrideOptionsTree(quib_change.quib, options, diverged_quib, children, override_removals)


def get_override_group_for_change(quib_change: Union[AssignmentToQuib, OverrideRemoval]) -> OverrideGroup:
    """
    Every assignment to a quib is translated at the end to a list of overrides to quibs in the graph.
    This function determines those overrides and returns them.
    When the assignment cannot be translated, CannotChangeQuibAtPathException is raised.
    Might raise AssignmentCancelledByUserException if a user cancels an override choice dialog.
    """
    options_tree = OverrideOptionsTree.from_quib_change(quib_change)
    if not options_tree:
        raise CannotChangeQuibAtPathException(quib_change)
    return options_tree.choose_overrides()


def get_overrides_for_quib_change_group(quib_changes: List[Union[AssignmentToQuib, OverrideRemoval]]) -> OverrideGroup:
    """
    Get all overrides for a group of assignments, filter them to leave out contradictory assignments
    (assignments that cause overrides in the same quibs) and return the remaining overrides.
    """
    all_overridden_quibs = set()
    result = OverrideGroup()
    for quib_change in quib_changes:
        try:
            override_group = get_override_group_for_change(quib_change)
        except CannotChangeQuibAtPathException:
            continue
        current_overridden_quibs = set(override.quib for override in override_group.quib_changes)
        if not ASSIGNMENT_RESTRICTIONS or not current_overridden_quibs.intersection(all_overridden_quibs):
            all_overridden_quibs.update(current_overridden_quibs)
            result.extend(override_group)
    return result
