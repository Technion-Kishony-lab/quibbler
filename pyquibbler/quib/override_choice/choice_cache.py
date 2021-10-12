from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any

from .override_dialog import OverrideChoice

if TYPE_CHECKING:
    from pyquibbler.quib import Quib
    from .override_choice import OverrideOptionsTree


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
                tuple(option.override.quib for option in options_tree.options),
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

    def clear(self):
        self._map.clear()
