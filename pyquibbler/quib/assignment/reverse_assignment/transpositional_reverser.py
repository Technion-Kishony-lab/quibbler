from __future__ import annotations

import numpy

import numpy as np
from operator import getitem
from typing import Dict, List, TYPE_CHECKING, Union, Any

from pyquibbler.quib.assignment import Assignment, IndicesAssignment
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import recursively_run_func_on_object

from .reverser import Reversal, Reverser
from ..assignment import QuibWithAssignment

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class TranspositionalReverser(Reverser):
    """
    In charge of reversing all functions which move elements around from it's arguments WITHOUT performing
    any mathematical operations between them.
    """

    SUPPORTED_FUNCTIONS = [
        np.rot90,
        np.concatenate,
        getitem
    ]

    def _get_quibs_to_ids(self) -> Dict[Quib, int]:
        """
        Get a mapping between quibs and their unique ids (these ids are only constant for the particular
        instance of the transpositional reverser)
        """
        return {potential_quib: i for i, potential_quib in enumerate(self._get_quibs_in_args())}

    def _get_quib_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """
        from pyquibbler.quib import Quib
        quibs_to_ids = self._get_quibs_to_ids()

        def replace_quib_with_id(obj):
            if isinstance(obj, Quib):
                return np.full(obj.get_shape().get_value(), quibs_to_ids[obj])
            return obj

        arguments = recursively_run_func_on_object(
            func=replace_quib_with_id,
            obj=self._args
        )
        return self._func(*arguments, *self._kwargs)

    def _get_bool_mask_representing_indices_in_result(self) -> Union[np.ndarray, bool]:
        """
        Get a boolean mask representing where the indices that were changed are in the result- this will be in
        same shape as the result
        """
        if not isinstance(self._assignment, IndicesAssignment):
            # If our indices is None, then the whole result is relevant- therefore we return a boolean mask of True
            return True
        return create_empty_array_with_values_at_indices(self._function_quib.get_shape().get_value(),
                                                         indices=self._indices,
                                                         value=True, empty_value=False)

    def _get_quibs_to_index_grids(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping between quibs and their indices grid
        """
        return {
            quib: np.indices(quib.get_shape().get_value())
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_to_masks(self):
        """
        Get a mapping between quibs and a bool mask representing all the elements that are relevant to them in the
        result (for the particular given changed indices)
        """
        quibs_to_ids = self._get_quibs_to_ids()
        quibs_mask = self._get_quib_ids_mask()

        def _build_quib_mask(quib: Quib):
            quib_mask_on_result = np.equal(quibs_mask, quibs_to_ids[quib])
            return np.logical_and(quib_mask_on_result, self._get_bool_mask_representing_indices_in_result())

        return {
            quib: _build_quib_mask(quib)
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_to_indices_at_dimension(self, dimension: int) -> Dict[Quib]:
        """
        Get a mapping of quibs to their referenced indices at a *specific dimension*
        """
        from pyquibbler.quib import Quib
        quibs_to_index_grids = self._get_quibs_to_index_grids()
        quibs_to_masks = self._get_quibs_to_masks()

        def replace_quib_with_index_at_dimension(q):
            if isinstance(q, Quib):
                return quibs_to_index_grids[q][dimension]
            return q

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_index_at_dimension,
            obj=self._args
        )

        indices_res = self._func(*new_arguments, **self._kwargs)

        return {
            quib: indices_res[quibs_to_masks[quib]]
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_to_indices_in_quibs(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after reversal of the
        indices relevant to the particular quib)
        """
        max_shape_length = max([len(quib.get_shape().get_value())
                                for quib in self._get_quibs_in_args()])
        quibs_to_indices_in_quibs = {}
        for i in range(max_shape_length):
            quibs_to_indices_at_dimension = self._get_quibs_to_indices_at_dimension(i)

            for quib, index in quibs_to_indices_at_dimension.items():
                quibs_to_indices_in_quibs.setdefault(quib, []).append(index)

        return quibs_to_indices_in_quibs

    def _get_quibs_to_relevant_result_values(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to values that were both referenced in `self._indices` and came from the
        corresponding quib
        """
        representative_result_value = self._get_representative_function_quib_result_with_value()
        quibs_to_masks = self._get_quibs_to_masks()

        def get_relevant_values_for_quib(quib):
            # Because `representative_result_value` may not be an np type, and we may not be able to successfully
            # convert it to an np type, we need to try returning the correct value WITHOUT subscription. For example, if
            # the mask is True or False we can immediately return the value or an empty array.
            # An example of this is if the `representative_result_value` is an int, and out masks are `True` or
            # `False`
            if np.all(quibs_to_masks[quib]):
                return representative_result_value
            if not np.any(quibs_to_masks[quib]):
                return np.array([])
            return representative_result_value[quibs_to_masks[quib]]

        return {
            quib: get_relevant_values_for_quib(quib)
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        quibs_to_indices_in_quibs = self._get_quibs_to_indices_in_quibs()
        quibs_to_results = self._get_quibs_to_relevant_result_values()

        return [
            QuibWithAssignment(
                quib=quib,
                assignment=IndicesAssignment(indices=quibs_to_indices_in_quibs[quib], value=quibs_to_results[quib],
                                             field=self._assignment.field),

            )
            for quib in quibs_to_indices_in_quibs
        ]

