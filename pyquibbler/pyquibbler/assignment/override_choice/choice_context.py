from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


@dataclass(frozen=True)
class ChoiceContext:
    """
    The context in which a choice was taken.
    Implements __hash__ and __eq__ to allow caching of user override choices.
    A choice can be reused in the context of a new assignment, if the options are the same.
    The override options for an inversed quib might change because when different indices are assigned to, the
    inversion tree might change (for example if one of the quib's parents is concat).
    """
    quibs_available_for_override: Tuple[Quib, ...]
    can_diverge: bool
