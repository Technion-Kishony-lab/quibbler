import numpy as np
from operator import getitem
from typing import List, Optional, Any, Callable, Dict

from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values

from pyquibbler.quib.function_quibs.default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, \
    SupportedFunction
from pyquibbler.quib.assignment.assignment import PathComponent


class TranspositionalFunctionQuib(DefaultFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A quib that represents any transposition function- a function that moves elements (but commits no operation on
    them)
    """
    SUPPORTED_FUNCTIONS = {
        np.rot90: SupportedFunction({0}),
        np.concatenate: SupportedFunction({0}),
        np.repeat: SupportedFunction({0}),
        np.full: SupportedFunction({1}),
        getitem: SupportedFunction({0}),
        np.reshape: SupportedFunction({0}),
        np.ravel: SupportedFunction({0}),
    }

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
            if isinstance(arg, Quib) and arg in self.get_data_source_quibs() else arg
            for arg in self._args
        ]

    def _get_quibs_to_ids(self) -> Dict[Quib, int]:
        """
        Get a mapping between quibs and their unique ids (these ids are only constant for the particular
        instance of the transpositional inverser)
        """
        return {potential_quib: i
                for i, potential_quib in enumerate(self.get_data_source_quibs())}

    def _get_quib_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """
        quibs_to_ids = self._get_quibs_to_ids()

        def replace_quib_with_id(obj):
            if isinstance(obj, Quib) and obj in self.get_data_source_quibs():
                return np.full(obj.get_shape().get_value(), quibs_to_ids[obj])
            return obj

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_id,
            obj=self._args
        )

        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)

    def _get_quibs_to_index_grids(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping between quibs and their indices grid
        """
        return {
            quib: np.indices(quib.get_shape().get_value())
            for quib in self.get_data_source_quibs()
        }

    def _get_quibs_to_masks(self):
        """
        Get a mapping between quibs and a bool mask representing all the elements that are relevant to them in the
        result
        """
        quibs_to_ids = self._get_quibs_to_ids()
        quibs_mask = self._get_quib_ids_mask()

        def _build_quib_mask(quib: Quib):
            return np.equal(quibs_mask, quibs_to_ids[quib])

        return {
            quib: _build_quib_mask(quib)
            for quib in self.get_data_source_quibs()
        }

    def _get_quibs_to_indices_at_dimension(self, dimension: int, relevant_indices_mask) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to their referenced indices at a *specific dimension*
        """
        quibs_to_index_grids = self._get_quibs_to_index_grids()
        quibs_to_masks = self._get_quibs_to_masks()

        def replace_quib_with_index_at_dimension(q):
            if isinstance(q, Quib) and q in self.get_data_source_quibs():
                return quibs_to_index_grids[q][dimension]
            return q

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_index_at_dimension,
            obj=self._args
        )

        indices_res = call_func_with_quib_values(self._func, new_arguments, self._kwargs)

        try:
            return {
                quib: indices_res[np.logical_and(quibs_to_masks[quib], relevant_indices_mask)]
                for quib in self.get_data_source_quibs()
            }
        except Exception:
            print(1)
            raise

    def get_quibs_to_indices_in_quibs(self, filtered_indices_in_result: Any) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after inversion of the
        indices relevant to the particular quib)
        """
        relevant_indices_mask = create_empty_array_with_values_at_indices(
            indices=filtered_indices_in_result,
            shape=self.get_shape().get_value(),
            value=True,
            empty_value=False
        )
        quibs = self.get_data_source_quibs()
        max_shape_length = max([len(quib.get_shape().get_value())
                                for quib in quibs]) if len(quibs) > 0 else 0
        # Default is to set all - if we have a shape we'll change this
        quibs_to_indices_in_quibs = {
            quib: None for quib in quibs
        }
        for i in range(max_shape_length):
            quibs_to_indices_at_dimension = self._get_quibs_to_indices_at_dimension(i, relevant_indices_mask)

            for quib, index in quibs_to_indices_at_dimension.items():
                if quibs_to_indices_in_quibs[quib] is None:
                    quibs_to_indices_in_quibs[quib] = tuple()
                quibs_to_indices_in_quibs[quib] = (*quibs_to_indices_in_quibs[quib], index)

        return {
            quib: indices
            for quib, indices in quibs_to_indices_in_quibs.items()
            if indices is None or all(
                len(dim) > 0
                for dim in indices
            )
        }

    def _get_source_paths_of_quibs_given_path(self, filtered_path_in_result: List[PathComponent]) \
            -> Dict[Quib, List[PathComponent]]:
        working_component = filtered_path_in_result[0].component if len(filtered_path_in_result) > 0 else True
        quibs_to_indices = self.get_quibs_to_indices_in_quibs(working_component)
        return {
            quib: [PathComponent(component=quibs_to_indices[quib], indexed_cls=np.ndarray)]
            if quibs_to_indices[quib] is not None else []
            for quib in quibs_to_indices
        }

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        """
        Translate the invalidation path to it's location after passing through the current function quib.
        If that path represents anything (ie any indices intersecting with the invalidation exist in the result),
        invalidate the children with the resulting indices.

        For example, if we have a rotate function, replace the arguments with a grid representing
        the arguments' indices that intersect with the invalidation path, and see where those indices land in the result
        If any indices exist in the result, invalidate all children with the resulting indices (or, in this
        implementation, a boolean mask representing them)
        """

        def _replace_arg_with_corresponding_mask_or_arg(q):
            if isinstance(q, Quib) and q in self.get_data_source_quibs():
                if q is quib:
                    return self._get_source_shaped_bool_mask(q, indices)
                else:
                    return np.full(q.get_shape().get_value(), False)
            return q

        new_arguments = recursively_run_func_on_object(
            func=_replace_arg_with_corresponding_mask_or_arg,
            obj=self._args
        )
        return call_func_with_quib_values(self._func, new_arguments, self._kwargs)

    def _get_path_for_children_invalidation(self, invalidator_quib: 'Quib',
                                            path: List[PathComponent]) -> Optional[List[PathComponent]]:
        """
        There are three things we can potentially do:
        1. Translate the invalidation path given the current function quib (eg if this function quib is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. In getitem, if the source quib is a list or a dict, check equality of indices and invalidation path-
           if so, continue with path[1:]
        3. Pass on the current path to all our children
        """
        if path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return path
        return super()._get_path_for_children_invalidation(invalidator_quib, path)

    def _get_quibs_to_relevant_result_values(self, assignment) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to values that were both referenced in `self._indices` and came from the
        corresponding quib
        """
        component = assignment.path[0].component if len(assignment.path) > 0 else True
        result_bool_mask = self._get_bool_mask_representing_indices_in_result(component)
        representative_result_value = self._get_representative_result(component, assignment.value)
        quibs_to_masks = self._get_quibs_to_masks()

        return {
            quib: representative_result_value[np.logical_and(quibs_to_masks[quib], result_bool_mask)]
            for quib in self.get_data_source_quibs()
        }
