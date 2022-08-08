from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Union

from pyquibbler.assignment import AssignmentToQuib


@dataclass
class QuibChangeWithOverrideRemovals:
    change: AssignmentToQuib
    override_removals: List[AssignmentToQuib]

    @property
    def quib(self):
        return self.change.quib


@dataclass
class OverrideGroup:
    """
    A group of overrides to be applied together, and the relevant override removals.
    When function_definitions a quib as a result of an upstream assignment,
    we remove overrides in all the indices that lead to the chosen override,
    so the override will actually cause the desired effect on the upstream quib.
    """
    quib_changes: List[AssignmentToQuib] = field(default_factory=list)

    def apply(self, on_drag: bool = False):
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        from pyquibbler.project import Project
        Project.get_or_create().start_pending_undo_group()
        with aggregate_redraw_mode():
            for quib_change in self.quib_changes:
                quib_change.apply()
        if not on_drag:
            Project.get_or_create().push_pending_undo_group_to_undo_stack()

    def __bool__(self):
        return len(self.quib_changes) > 0

    def extend(self, extension: Union[OverrideGroup, List[AssignmentToQuib]]):
        """
        Add quib changes from a list or another override group.
        """
        if isinstance(extension, OverrideGroup):
            self.quib_changes.extend(extension.quib_changes)
        elif isinstance(extension, list):
            self.quib_changes.extend(extension)
        else:
            raise TypeError(type(extension))
