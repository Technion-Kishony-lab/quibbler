from __future__ import annotations
from dataclasses import dataclass
from typing import List

from prometheus_client.decorator import contextmanager

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


WITHIN_TEMPORARY_APPLY_OVERRIDE_GROUP = False


class OverrideGroup(List[AssignmentToQuib]):
    """
    A group of overrides to be applied together, and the relevant override removals.
    When overriding a quib as a result of an upstream assignment,
    we remove overrides in all the indices that lead to the chosen override,
    so the override will actually cause the desired effect on the upstream quib.
    """
    def _apply_generator(self, temporarily: bool):
        with undo_group_mode(temporarily):
            with aggregate_redraw_mode(temporarily):
                for quib_change in self:
                    quib_change.apply()
                yield

    def apply(self):
        g = self._apply_generator(False)
        next(g)
        try:
            next(g)
        except StopIteration:
            pass

    @contextmanager
    def temporarily_apply(self):
        global WITHIN_TEMPORARY_APPLY_OVERRIDE_GROUP
        if WITHIN_TEMPORARY_APPLY_OVERRIDE_GROUP:
            yield
            return

        WITHIN_TEMPORARY_APPLY_OVERRIDE_GROUP = True
        try:
            yield from self._apply_generator(True)
        finally:
            WITHIN_TEMPORARY_APPLY_OVERRIDE_GROUP = False


def is_within_temporary_apply_override_group():
    return WITHIN_TEMPORARY_APPLY_OVERRIDE_GROUP
