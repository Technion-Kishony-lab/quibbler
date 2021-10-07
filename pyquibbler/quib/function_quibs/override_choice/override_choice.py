from __future__ import annotations
from dataclasses import dataclass
from typing import List, TYPE_CHECKING, Optional, Dict, Any
from pyquibbler.quib.assignment import QuibWithAssignment, CannotReverseUnknownFunctionException, reverse_function_quib

from .override_dialog import OverrideChoiceType, OverrideChoice, choose_override_dialog

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib, Quib


class ChoiceCache:
    def __init__(self):
        self._map: Dict[Any, OverrideChoice] = {}

    def _get_key(self, reversed_quib: FunctionQuib, options_tree: OverrideOptionsTree):
        return (reversed_quib,
                frozenset({id(option.quib) for option in options_tree.options}),
                options_tree.can_diverge)

    def store(self, choice: OverrideChoice, reversed_quib: FunctionQuib, options_tree: OverrideOptionsTree):
        self._map[self._get_key(reversed_quib, options_tree)] = choice

    def load(self, reversed_quib: FunctionQuib, options_tree: OverrideOptionsTree) -> Optional[OverrideChoice]:
        return self._map.get(self._get_key(reversed_quib, options_tree))


@dataclass
class OverrideOptionsTree:
    _CHOICE_CACHE = ChoiceCache()

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

    def _try_load_choice(self, reversed_quib: FunctionQuib) -> Optional[OverrideChoice]:
        choice = self._CHOICE_CACHE.load(reversed_quib, self)
        if choice is not None and choice.choice_type is OverrideChoiceType.OVERRIDE:
            chosen_quib = choice.chosen_override.quib
            option = next(option for option in self.options if option.quib is chosen_quib)
            choice = OverrideChoice(choice.choice_type, option)
        return choice

    def _store_choice(self, reversed_quib: FunctionQuib, choice: OverrideChoice):
        self._CHOICE_CACHE.store(choice, reversed_quib, self)

    def get_override_choice(self, reversed_quib: FunctionQuib) -> OverrideChoice:
        if len(self.options) == 1 and not self.can_diverge:
            return OverrideChoice(OverrideChoiceType.OVERRIDE, self.options[0])
        choice = self._try_load_choice(reversed_quib)
        if choice is None:
            choice = choose_override_dialog(self.options, self.can_diverge)
            if choice.choice_type is not OverrideChoiceType.CANCEL:
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

        assert self.can_diverge
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
        return OverrideOptionsTree(options, None if not children else last_reversal.quib, children)
