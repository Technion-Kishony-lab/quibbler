from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING, Union

from pyquibbler.quib.assignment import QuibWithAssignment
from pyquibbler.quib.assignment.assignment import PathComponent

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


@dataclass
class OverrideWithOverrideRemovals:
    override: QuibWithAssignment
    override_removals: List[OverrideRemoval]


@dataclass
class OverrideRemoval:
    """
    Removal of overrides in a specific path on a specific quib.
    """
    quib: Quib
    path: List[PathComponent]

    def apply(self, invalidate_and_redraw: bool = True):
        self.quib.remove_override(self.path, invalidate_and_redraw=invalidate_and_redraw)

    @classmethod
    def from_inversion(cls, inversion: QuibWithAssignment):
        return cls(inversion.quib, inversion.assignment.path)


@dataclass
class OverrideGroup:
    """
    A group of overrides to be applied together, and the relevant override removals.
    When overriding a quib as a result of an upstream assignment,
    we remove overrides in all the indices that lead to the chosen override,
    so the override will actually cause the desired effect on the upstream quib.
    """
    overrides: List[QuibWithAssignment] = field(default_factory=list)
    override_removals: List[OverrideRemoval] = field(default_factory=list)

    def apply(self, invalidate_and_redraw_override_removals: bool = True):
        for override in self.overrides:
            override.override()
        for override_removal in self.override_removals:
            override_removal.apply(invalidate_and_redraw=invalidate_and_redraw_override_removals)

    def __bool__(self):
        return len(self.overrides) > 0 or len(self.override_removals) > 0

    def extend(self, extension: Union[OverrideGroup, List[OverrideRemoval]]):
        """
        Add overrides and override removals.
        """
        if isinstance(extension, OverrideGroup):
            self.overrides.extend(extension.overrides)
            self.override_removals.extend(extension.override_removals)
        elif isinstance(extension, list) and extension and isinstance(extension[0], OverrideRemoval):
            self.override_removals.extend(extension)
        else:
            raise TypeError()
