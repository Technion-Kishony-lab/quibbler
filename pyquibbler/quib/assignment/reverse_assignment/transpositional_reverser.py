from __future__ import annotations
import functools
import numpy as np
from operator import getitem
from typing import Dict, List, TYPE_CHECKING, Union, Callable, Any

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values, \
    iter_objects_of_type_in_object_shallowly

from .reverser import Reverser
from ..assignment import QuibWithAssignment

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class TranspositionalReverser(Reverser):
    """
    In charge of reversing all functions which move elements around from it's arguments WITHOUT performing
    any mathematical operations between them.
    """

    SUPPORTED_FUNCTIONS_TO_POTENTIALLY_CHANGED_QUIB_INDICES = {
        np.rot90: {0},
        np.concatenate: {0},
        np.repeat: {0},
        np.full: {1},
        getitem: {0},
        np.reshape: {0}
    }

    SUPPORTED_FUNCTIONS = list(SUPPORTED_FUNCTIONS_TO_POTENTIALLY_CHANGED_QUIB_INDICES.keys())

    @functools.lru_cache()
    def _get_quibs_which_can_change(self):
        """
        Return a list of quibs that can potentially change as a result of the transpositional function- this does NOT
        necessarily mean these quibs will in fact be changed.

        For example, in `np.repeat(q1, q2)`, where q1 is a numpy array quib
        and q2 is a number quib with amount of times to repeat, q2 cannot in any
        situation be changed by a change in `np.repeat`'s result. So only `q1` would be returned.
        """
        from pyquibbler.quib import Quib
        potentially_changed_quib_indices = self.SUPPORTED_FUNCTIONS_TO_POTENTIALLY_CHANGED_QUIB_INDICES[self._func]
        quibs = []
        for i, arg in enumerate(self._args):
            if i in potentially_changed_quib_indices:
                quibs.extend(iter_objects_of_type_in_object_shallowly(Quib, arg))
        return quibs

    def _replace_quibs_in_arguments_which_can_potentially_change(self, replace_func: Callable[['Quib'], Any]):
        """
        Get a new list of arguments where all quibs that can be potentially changed by the transposition func
        are replaced by the given function
        """
        from pyquibbler.quib import Quib
        return [
            recursively_run_func_on_object(
                func=replace_func,
                obj=arg
            )
            if isinstance(arg, Quib) and arg in self._get_quibs_which_can_change() else arg
            for arg in self._args
        ]

    def _get_quibs_to_ids(self) -> Dict[Quib, int]:
        """
        Get a mapping between quibs and their unique ids (these ids are only constant for the particular
        instance of the transpositional reverser)
        """
        return {potential_quib: i
                for i, potential_quib in enumerate(self._get_quibs_which_can_change())}

    def _get_quib_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """
        from pyquibbler.quib import Quib
        quibs_to_ids = self._get_quibs_to_ids()

        def replace_quib_with_id(obj):
            if obj in self._get_quibs_which_can_change():
                return np.full(obj.get_shape().get_value(), quibs_to_ids[obj])
            return obj

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_id,
            obj=self._args
        )
        # new_arguments = self._replace_quibs_in_arguments_which_can_potentially_change(replace_quib_with_id)

        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)

    def _get_bool_mask_representing_indices_in_result(self) -> Union[np.ndarray, bool]:
        """
        Get a boolean mask representing where the indices that were changed are in the result- this will be in
        same shape as the result
        """
        return create_empty_array_with_values_at_indices(self._function_quib.get_shape().get_value(),
                                                         indices=self._working_indices,
                                                         value=True, empty_value=False)

    def _get_quibs_to_index_grids(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping between quibs and their indices grid
        """
        return {
            quib: np.indices(quib.get_shape().get_value())
            for quib in self._get_quibs_which_can_change()
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
            for quib in self._get_quibs_which_can_change()
        }

    def _get_quibs_to_indices_at_dimension(self, dimension: int) -> Dict[Quib]:
        """
        Get a mapping of quibs to their referenced indices at a *specific dimension*
        """
        from pyquibbler.quib import Quib
        quibs_to_index_grids = self._get_quibs_to_index_grids()
        quibs_to_masks = self._get_quibs_to_masks()

        def replace_quib_with_index_at_dimension(q):
            if q in self._get_quibs_which_can_change():
                return quibs_to_index_grids[q][dimension]
            return q

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_index_at_dimension,
            obj=self._args
        )

        indices_res = call_func_with_quib_values(self._func, new_arguments, self._kwargs)

        return {
            quib: indices_res[quibs_to_masks[quib]]
            for quib in self._get_quibs_which_can_change()
        }

    def _get_quibs_to_indices_in_quibs(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after reversal of the
        indices relevant to the particular quib)
        """
        quibs = self._get_quibs_which_can_change()
        max_shape_length = max([len(quib.get_shape().get_value())
                                for quib in quibs]) if len(quibs) > 0 else 0
        # Default is to set all - if we have a shape we'll change this
        quibs_to_indices_in_quibs = {
            quib: ... for quib in quibs
        }
        for i in range(max_shape_length):
            quibs_to_indices_at_dimension = self._get_quibs_to_indices_at_dimension(i)

            for quib, index in quibs_to_indices_at_dimension.items():
                if quibs_to_indices_in_quibs[quib] is ...:
                    quibs_to_indices_in_quibs[quib] = tuple()
                quibs_to_indices_in_quibs[quib] = (*quibs_to_indices_in_quibs[quib], index)

        return {
            quib: indices
            for quib, indices in quibs_to_indices_in_quibs.items()
            if indices is ... or all(
                len(dim) > 0
                for dim in indices
            )
        }

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
            for quib in self._get_quibs_which_can_change()
        }

    def _is_getitem_with_field(self):
        """
        Check's whether we have at hand a function quib which represents a __getitem__ with the indices being a string
        """
        from pyquibbler.quib import Quib
        return self._func == getitem and isinstance(self._args[1], str) and isinstance(self._args[0], Quib)

    def _is_getitem_of_quib_list(self):
        """
        Check's whether we have at hand a function quib which represents a __getitem__ with the indices being a string
        """
        from pyquibbler.quib import Quib
        return self._func == getitem and isinstance(self._args[0], Quib) and issubclass(self._args[0].get_type(), list)

    def _build_quibs_with_assignments_for_getitem(self) -> List[QuibWithAssignment]:
        """
        We're in a situation where we can't compute any any translation of indices
        Because of this, we put all pieces of the getitem in the path- making sure to put the field BEFORE the indexing
        (keeping it in the same order as it was, so we don't reverse the indices in the next reversal)
        """
        return [QuibWithAssignment(
            quib=self._args[0],
            assignment=Assignment(paths=[self._args[1], self._working_indices],
                                  value=self._value)
        )]

    def _build_quibs_with_assignments_for_generic_case(self) -> List[QuibWithAssignment]:
        """
        Build assignments for the generic case, in which we want to attempt translation of indices and values
        to the quib we're creating an assignment to.
        If the self.field is a string, we always look attempt to look at the array without it's structure quality,
        meaning our self.indices will always be True (as we're not dividing that last 'dimension').
        Because of this, we need to add self.field to the paths.
        """
        quibs_to_indices_in_quibs = self._get_quibs_to_indices_in_quibs()
        quibs_to_results = self._get_quibs_to_relevant_result_values()

        quibs_with_assignments = []
        for quib in quibs_to_indices_in_quibs:
            quibs_with_assignments.append(QuibWithAssignment(
                quib=quib,
                assignment=Assignment(paths=[quibs_to_indices_in_quibs[quib]],
                                      value=quibs_to_results[quib])
            ))
        return quibs_with_assignments

    def get_reversed_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        if self._is_getitem_with_field() or self._is_getitem_of_quib_list():
            return self._build_quibs_with_assignments_for_getitem()

        return self._build_quibs_with_assignments_for_generic_case()
