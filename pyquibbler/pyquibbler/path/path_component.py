from dataclasses import dataclass
from typing import Type, Any, List, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pyquibbler import Quib


@dataclass
class PathComponent:
    indexed_cls: Type
    component: Any
    extract_element_out_of_array: bool = False

    def referencing_field_in_field_array(self, type_) -> bool:
        """
        Indicated whether the component references a field in a field array
        """
        return (issubclass(type_, np.ndarray) and
                (isinstance(self.component, str) or
                 (isinstance(self.component, list) and isinstance(self.component[0], str))))

    def is_nd_reference(self):
        return isinstance(self.component, (tuple, list, np.ndarray))

    def is_compound(self):
        return isinstance(self.component, tuple) and len(self.component) > 1

    def get_multi_step_path(self) -> 'Path':
        if not self.is_compound():
            return [self]
        return list(PathComponent(self.indexed_cls, cmp) for cmp in self.component)

Path = List[PathComponent]

Paths = List[Path]



