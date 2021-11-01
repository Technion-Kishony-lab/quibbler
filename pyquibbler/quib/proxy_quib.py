from typing import Set, Optional, List, Any

from pyquibbler import Assignment
from pyquibbler.quib import Quib
from pyquibbler.quib.assignment import PathComponent


class ProxyQuib(Quib):

    def __init__(self, quib):
        super().__init__()
        self._quib: Quib = quib

    def _get_inner_value_valid_at_path(self, path: Optional[List[PathComponent]]) -> Any:
        return self._quib.get_value_valid_at_path(path=path)

    @property
    def parents(self) -> Set[Quib]:
        return self._quib.parents

    def assign(self, assignment: Assignment) -> None:
        self._quib.assign(assignment)

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        return []
