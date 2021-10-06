from __future__ import annotations
from typing import List, Tuple, TYPE_CHECKING

from pyquibbler.quib.assignment import QuibWithAssignment

from .override_dialog import OverrideChoice, choose_override_dialog

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib

OverrideOptions = List[QuibWithAssignment]
DivergedOptions = List[Tuple[OverrideOptions, 'DivergedOptions']]


def get_override_choice(override_options: List[QuibWithAssignment],
                        can_diverge: bool) -> Tuple[OverrideChoice, QuibWithAssignment]:
    if len(override_options) == 1 and not can_diverge:
        return OverrideChoice.OVERRIDE, override_options[0]
    return choose_override_dialog(override_options, can_diverge)


def choose_overrides_from_diverged_reverse_assignment(diverged_options: DivergedOptions) -> OverrideOptions:
    chosen_overrides = []
    for next_override_options, next_diverged_options in diverged_options:
        new_overrides = choose_overrides(next_override_options, next_diverged_options)
        if not new_overrides:
            # One of the diverged branches was cancelled, so we cancel the whole assignment
            return []
        chosen_overrides.extend(new_overrides)
    return chosen_overrides


def choose_overrides(reversed_quib: FunctionQuib,
                     override_options: List[QuibWithAssignment],
                     diverged_options: DivergedOptions) -> List[QuibWithAssignment]:
    can_diverge = len(diverged_options) > 0
    override_choice = OverrideChoice.DIVERGE
    if override_options:
        override_choice, chosen_override = get_override_choice(override_options, can_diverge)
        if override_choice is OverrideChoice.CANCEL:
            return []
        elif override_choice is OverrideChoice.OVERRIDE:
            # if override_choice is OverrideChoice.OVERRIDE, metadata is the choice index
            return [chosen_override]

    assert can_diverge
    assert override_choice is OverrideChoice.DIVERGE
    return choose_overrides_from_diverged_reverse_assignment(diverged_options)
