from __future__ import annotations
import functools
import numpy as np
from operator import getitem
from typing import Dict, List, TYPE_CHECKING, Union, Callable, Any, Tuple

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values, \
    iter_objects_of_type_in_object_shallowly

from .inverser import Inverser
from ..assignment import QuibWithAssignment, PathComponent

if TYPE_CHECKING:
    from ...function_quibs.transpositional_function_quib import TranspositionalFunctionQuib
    from pyquibbler.quib import Quib


class TranspositionalInverser(Inverser):
    """
    In charge of reversing all functions which move elements around from it's arguments WITHOUT performing
    any mathematical operations between them.
    """

    def _get_quibs_which_can_change(self):
        """
        Helper method to get quibs which can change (are "data" quibs)
        from function quib- see docs of TranspositionalFunctionQuib's `get_quibs_which_can_change`
         to understand functionality
        """
        return self._function_quib.get_quibs_which_can_change()

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
        instance of the transpositional inverser)
        """
        return {potential_quib: i
                for i, potential_quib in enumerate(self._get_quibs_which_can_change())}

    def _get_quib_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """
        quibs_to_ids = self._get_quibs_to_ids()

        def replace_quib_with_id(obj):
            if obj in self._get_quibs_which_can_change():
                return np.full(obj.get_shape().get_value(), quibs_to_ids[obj])
            return obj

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_id,
            obj=self._args
        )

        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)

    def _get_bool_mask_representing_indices_in_result(self) -> Union[np.ndarray, bool]:
        """
        Get a boolean mask representing where the indices that were changed are in the result- this will be in
        same shape as the result
        """
        return create_empty_array_with_values_at_indices(self._function_quib.get_shape().get_value(),
                                                     indices=self._working_indices, value=True, empty_value=False)

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
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after inversal of the
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

        return {
            quib: representative_result_value[quibs_to_masks[quib]]
            for quib in self._get_quibs_which_can_change()
        }

    def _build_quibs_with_assignments_for_getitem(self) -> List:
        """
        We're in a situation where we can't compute any any translation of indices
        Because of this, we put all pieces of the getitem in the path- making sure to put the field BEFORE the indexing
        (keeping it in the same order as it was, so we don't inverse the indices in the next inversal)
        """
        return [QuibWithAssignment(
            quib=self._args[0],
            assignment=Assignment(path=[PathComponent(indexed_cls=self._args[0].get_type(),
                                                      component=self._args[1]), *self._assignment.path],
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
                assignment=Assignment(path=[PathComponent(indexed_cls=np.ndarray,
                                                          component=quibs_to_indices_in_quibs[quib]),
                                            *self._assignment.path[1:]],
                                      value=quibs_to_results[quib])
            ))
        return quibs_with_assignments

    def _next_path_component_has_translatable_np_indices(self):
        """
        Check's whether we have at hand a function quib which represents a __getitem__ with the indices being fancy
        indexes [and the resulting type being an ndarray]
        """
        return (issubclass(self._function_quib.get_type(), np.ndarray)
                and not self._assignment.path[0].references_field_in_field_array())

    def _is_getitem_with_field(self):
        return \
            PathComponent(indexed_cls=self._function_quib.get_type(), component=self._args[1]).references_field_in_field_array()

    def get_inversed_quibs_with_assignments(self) -> List[QuibWithAssignment]:
        if (self._func == getitem and
                (
                        not self._next_path_component_has_translatable_np_indices()
                        or
                        self._is_getitem_with_field()
                )
        ):
            # We are a getitem and can't translate the indices- simply add the getitem's item as the first item
            # before the rest of the path
            return self._build_quibs_with_assignments_for_getitem()

        return self._build_quibs_with_assignments_for_generic_case()
