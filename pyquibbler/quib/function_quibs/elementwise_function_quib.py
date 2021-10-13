from typing import TYPE_CHECKING, List, Tuple, Any

import numpy as np

from .default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.inverse_assignment import ElementWiseInverser

from ..assignment.assignment import PathComponent
from ..assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices

if TYPE_CHECKING:
    from pyquibbler.quib.assignment import Assignment
    from pyquibbler.quib import Quib


class ElementWiseFunctionQuib(DefaultFunctionQuib):
    """
    A quib representing an element wise mathematical operation- this includes any op that can map an output element
    back to an input element, and the operation can be inversed per element
    """

    def _create_bool_mask_representing_invalidator_quib_at_indices_in_result(self,
                                                                             invalidator_quib: 'Quib',
                                                                             indices: Any):
        return np.broadcast_to(create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=invalidator_quib.get_shape().get_value()
        ), self.get_shape().get_value())

    def _invalidate_quib_with_children_at_path(self, invalidator_quib: 'Quib', path: List['PathComponent']):
        working_component = path[0]
        if working_component.references_field_in_field_array():
            return super(ElementWiseFunctionQuib, self)._invalidate_quib_with_children_at_path(self, path)

        new_component = self._create_bool_mask_representing_invalidator_quib_at_indices_in_result(invalidator_quib,
                                                                                                  working_component.
                                                                                                  component)

        new_path = [
            PathComponent(component=new_component, indexed_cls=self.get_type()),
            *path[1:]
        ]
        super(ElementWiseFunctionQuib, self)._invalidate_quib_with_children_at_path(invalidator_quib, new_path)

    def get_inversals_for_assignment(self, assignment: 'Assignment'):
        return ElementWiseInverser(
            assignment=assignment,
            function_quib=self
        ).get_inversed_quibs_with_assignments()
