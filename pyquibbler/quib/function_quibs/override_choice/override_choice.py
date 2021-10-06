from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional
from pyquibbler.quib.assignment import QuibWithAssignment, CannotReverseUnknownFunctionException, reverse_function_quib

from .override_dialog import OverrideChoiceType, OverrideChoice, choose_override_dialog

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib


@dataclass
class OverrideOptionsTree:
    options: List[QuibWithAssignment]
    diverged_quib: Optional[FunctionQuib]
    children: List[OverrideOptionsTree]

    def __post_init__(self):
        if self.children:
            assert self.diverged_quib is not None

    @property
    def _can_diverge(self):
        return len(self.children) > 0

    def __bool__(self):
        return len(self.options) > 0 or self._can_diverge

    def _try_load_choice(self, reversed_quib: FunctionQuib) -> Optional[OverrideChoice]:
        return None

    def _store_choice(self, reversed_quib: FunctionQuib, choice: OverrideChoice):
        pass

    def get_override_choice(self, reversed_quib: FunctionQuib) -> OverrideChoice:
        if len(self.options) == 1 and not self._can_diverge:
            return OverrideChoice(OverrideChoiceType.OVERRIDE, self.options[0])
        choice = self._try_load_choice(reversed_quib)
        if choice is None:
            choice = choose_override_dialog(self.options, self._can_diverge)
            self._store_choice(reversed_quib, choice)
        return choice

    def choose_overrides_from_diverged_reverse_assignment(self,
                                                          reversed_quib: FunctionQuib) -> List[QuibWithAssignment]:
        chosen_overrides = []
        for child in self.children:
            new_overrides = child.choose_overrides(reversed_quib)
            if not new_overrides:
                # One of the diverged branches was cancelled, so we cancel the whole assignment
                return []
            chosen_overrides.extend(new_overrides)
        return chosen_overrides

    def choose_overrides(self, reversed_quib: FunctionQuib) -> List[QuibWithAssignment]:
        choice_type = OverrideChoiceType.DIVERGE
        if self.options:
            choice = self.get_override_choice(reversed_quib)
            choice_type = choice.choice_type
            if choice_type is OverrideChoiceType.CANCEL:
                return []
            elif choice_type is OverrideChoiceType.OVERRIDE:
                # if override_choice is OverrideChoiceType.OVERRIDE, metadata is the choice index
                return [choice.chosen_override]

        assert self._can_diverge
        assert choice_type is OverrideChoiceType.DIVERGE
        return self.choose_overrides_from_diverged_reverse_assignment(self.diverged_quib)

    @classmethod
    def _get_next_reversals(cls, reversal: QuibWithAssignment):
        from pyquibbler.quib import FunctionQuib
        if isinstance(reversal.quib, FunctionQuib):
            try:
                return reverse_function_quib(reversal.quib, reversal.assignment)
            except CannotReverseUnknownFunctionException:
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
                children = []
                break
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
        return OverrideOptionsTree(options, last_reversal, children)
