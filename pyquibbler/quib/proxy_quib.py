from __future__ import annotations
from typing import Set, Optional, List, Any, TYPE_CHECKING

from pyquibbler.quib.quib import Quib

if TYPE_CHECKING:
    from pyquibbler.quib import Assignment, PathComponent, QuibWithAssignment


class ProxyQuib(Quib):
    """
    A proxy quib wraps another quib allowing only and ensures that no invalidations go through it. This is useful when
    attempting to separate a quib from it's children.
    If the proxy quib is assigned to it DOES reverse assign- meaning a proxy quib works backwards in every manner,
    but never forwards (ie invalidation)
    """

    def __init__(self, quib):
        super().__init__()
        self._quib: Quib = quib
        quib.add_child(self)

    def _get_inner_value_valid_at_path(self, path: Optional[List[PathComponent]]) -> Any:
        return self._quib.get_value_valid_at_path(path=path)

    @property
    def parents(self) -> Set[Quib]:
        return self._quib.parents

    def assign(self, assignment: Assignment) -> None:
        self._quib.assign(assignment)

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        # We never invalidate our children
        return []

    def get_inversions_for_assignment(self, assignment: Assignment) -> List[QuibWithAssignment]:
        return [QuibWithAssignment(quib=self._quib, assignment=assignment)]
