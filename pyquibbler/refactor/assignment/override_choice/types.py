from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Union

from pyquibbler.project import Project
from pyquibbler.refactor.assignment import AssignmentToQuib, QuibChange, CannotReverseException
from pyquibbler.refactor.path.path_component import PathComponent
from pyquibbler.refactor.assignment.assignment import Override


@dataclass
class QuibChangeWithOverrideRemovals:
    change: QuibChange
    override_removals: List[OverrideRemoval]

    @property
    def quib(self):
        return self.change.quib


@dataclass(frozen=True)
class OverrideRemoval(QuibChange):
    """
    Removal of overrides in a specific path on a specific quib.
    """
    _path: List[PathComponent]

    @property
    def path(self):
        return self._path

    def apply(self, invalidate_and_redraw: bool = True):
        self.quib.remove_override(self.path, invalidate_and_redraw=invalidate_and_redraw)

    @classmethod
    def from_quib_change(cls, change: QuibChange):
        return cls(change.quib, change.path)

    def get_inversions(self, return_empty_list_instead_of_raising=False) -> List[OverrideRemoval]:
        try:
            return self.quib.get_inversions_for_override_removal(self)
        except CannotReverseException:
            if return_empty_list_instead_of_raising:
                return []
            raise


@dataclass
class OverrideGroup:
    """
    A group of overrides to be applied together, and the relevant override removals.
    When function_definitions a quib as a result of an upstream assignment,
    we remove overrides in all the indices that lead to the chosen override,
    so the override will actually cause the desired effect on the upstream quib.
    """
    quib_changes: List[Union[Override, OverrideRemoval]] = field(default_factory=list)

    def apply(self):
        from pyquibbler.refactor.quib.graphics.redraw import aggregate_redraw_mode
        with Project.get_or_create().start_undo_group():
            with aggregate_redraw_mode():
                for quib_change in self.quib_changes:
                    assert not isinstance(quib_change, AssignmentToQuib)
                    quib_change.apply()

    def __bool__(self):
        return len(self.quib_changes) > 0

    def extend(self, extension: Union[OverrideGroup, List[OverrideRemoval]]):
        """
        Add quib changes from a list or another override group.
        """
        if isinstance(extension, OverrideGroup):
            self.quib_changes.extend(extension.quib_changes)
        elif isinstance(extension, list):
            self.quib_changes.extend(extension)
        else:
            raise TypeError(type(extension))
