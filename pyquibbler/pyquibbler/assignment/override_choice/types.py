from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Union

from pyquibbler.assignment import AssignmentToQuib
from pyquibbler.project.undo_group import undo_group_mode
from pyquibbler.quib.graphics import aggregate_redraw_mode


@dataclass
class QuibChangeWithOverrideRemovals:
    change: AssignmentToQuib
    override_removals: List[AssignmentToQuib]

    @property
    def quib(self):
        return self.change.quib


class OverrideGroup(List[AssignmentToQuib]):
    """
    A group of overrides to be applied together, and the relevant override removals.
    When overriding a quib as a result of an upstream assignment,
    we remove overrides in all the indices that lead to the chosen override,
    so the override will actually cause the desired effect on the upstream quib.
    """
    def apply(self, temporarily: bool = False):
        with undo_group_mode(temporarily):
            with aggregate_redraw_mode(temporarily):
                for quib_change in self:
                    quib_change.apply()
