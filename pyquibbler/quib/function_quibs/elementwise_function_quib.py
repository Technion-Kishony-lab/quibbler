from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING, Any

from pyquibbler.quib.assignment.inverse_assignment import ElementWiseInverter

from .default_function_quib import DefaultFunctionQuib
from .indices_translator_function_quib import IndicesTranslatorFunctionQuib

if TYPE_CHECKING:
    from pyquibbler.quib.assignment import Assignment
    from pyquibbler.quib import Quib


class ElementWiseFunctionQuib(DefaultFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A quib representing an element wise mathematical operation- this includes any op that can map an output element
    back to an input element, and the operation can be inversed per element
    """
    SUPPORTED_FUNCTIONS = None

    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        """
        Create a boolean mask representing the invalidator quib at certain indices in the result.
        For a simple operation (eg `invalidator=[1, 2, 3]`, `invalidator + [2, 3, 4]`, and we invalidate `(0, 0)`),
        the `True`'s will be in the location of the indices (`[True, False, False]`)- but if
        the invalidator quib was broadcasted, we need to make sure we get a boolean mask representing where the indices
        were in the entire result.

        For example- if we have
        ```
        invalidator_quib = [[1, 2, 3]]
        sum_ = invalidator_quib + [[1], [2], [3]]
        ```
        and we invalidate at (0, 0), we need to create a mask broadcasted like the argument was, ie
        [[True, False, False],
         [True, False, False],
         [True, False, False]]
        """
        bool_mask = self._get_source_shaped_bool_mask(invalidator_quib, indices)
        return np.broadcast_to(bool_mask, self.get_shape().get_value())

    def _get_path_for_children_invalidation(self, invalidator_quib: 'Quib',
                                            path: List['PathComponent']) -> Optional[List['PathComponent']]:
        working_component = path[0]
        new_component = self._create_bool_mask_representing_quib_at_indices_in_result(invalidator_quib,
                                                                                      working_component.
                                                                                      component)

        new_path = [
            PathComponent(component=new_component, indexed_cls=self.get_type()),
            *path[1:]
        ]
        return new_path

    def _get_translated_argument_quib_path_at_path(self, quib: 'Quib', arg_index: int, path: List[PathComponent]):
        if path is None:
            working_component = False
        else:
            working_component = path[0].component if len(path) > 0 else True
        bool_mask = self._create_bool_mask_representing_quib_at_indices_in_result(indices=working_component, quib=quib)
        return [PathComponent(
            component=bool_mask,
            indexed_cls=quib.get_type()
        )]

    def get_inversions_for_assignment(self, assignment: 'Assignment'):
        return ElementWiseInverter(
            assignment=assignment,
            function_quib=self
        ).get_inversed_quibs_with_assignments()
