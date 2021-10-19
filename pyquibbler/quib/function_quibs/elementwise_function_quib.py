from __future__ import annotations
import numpy as np
from typing import TYPE_CHECKING, Any, List

from pyquibbler.quib.assignment.inverse_assignment import ElementWiseInverter

from .default_function_quib import DefaultFunctionQuib
from .indices_translator_function_quib import IndicesTranslatorFunctionQuib
from ..assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from ..utils import call_func_with_quib_values

from pyquibbler.quib.assignment import Assignment, PathComponent
if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class ElementWiseFunctionQuib(DefaultFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A quib representing an element wise mathematical operation- this includes any op that can map an output element
    back to an input element, and the operation can be inversed per element
    """
    SUPPORTED_FUNCTIONS = None

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        """
        # TODO change comment
        Create a boolean mask representing the quib at certain indices in the result.
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

    def get_inversions_for_assignment(self, assignment: 'Assignment'):
        return ElementWiseInverter(
            assignment=assignment,
            function_quib=self
        ).get_inversed_quibs_with_assignments()
