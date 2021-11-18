from dataclasses import dataclass

import numpy as np
from operator import getitem
from typing import List, Optional, Any, Callable, Dict, Tuple

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.utils import recursively_run_func_on_object, call_func_with_quib_values
from pyquibbler.quib.function_quibs import FunctionQuib
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices, convert_args_and_kwargs
from pyquibbler.quib.function_quibs.default_function_quib import DefaultFunctionQuib
from pyquibbler.quib.function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, \
    SupportedFunction
from pyquibbler.quib.assignment import PathComponent


def transpose_forward_translate(indices: Tuple[Any, ...], quib: FunctionQuib) -> Any:
    axes = quib.get_args_values().get('axes')
    if axes is None:
        axes = range(quib.get_ndim())[::-1]
    return tuple(indices[axis] for axis in axes)


@dataclass
class SupportedFunctionWithSimpleTranslation(SupportedFunction):
    forward_translate: Callable[[Tuple[Any, ...], FunctionQuib], Any]


class TranspositionalFunctionQuib(DefaultFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A quib that represents any transposition function- a function that moves elements (but commits no operation on
    them)
    """
    SUPPORTED_FUNCTIONS = {
        np.rot90: SupportedFunction({0}),
        np.repeat: SupportedFunction({0}),
        np.full: SupportedFunction({1}),
        getitem: SupportedFunction({0}),
        np.reshape: SupportedFunction({0}),
        np.ravel: SupportedFunction({0}),
        np.squeeze: SupportedFunction({0}),
        np.array: SupportedFunction({0}),
        np.asarray: SupportedFunction({0}),
        np.swapaxes: SupportedFunction({0}),
        np.expand_dims: SupportedFunction({0}),
        np.tile: SupportedFunction({0}),
        np.transpose: SupportedFunctionWithSimpleTranslation({0}, transpose_forward_translate),
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
            if isinstance(arg, Quib) and arg in self._get_data_source_quibs() else arg
            for arg in self._args
        ]

    def _get_quib_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """

        def replace_quib_with_id(obj):
            if isinstance(obj, Quib):
                return np.full(obj.get_shape(), id(obj))
            return obj

        args, kwargs = self._convert_data_sources_in_args(replace_quib_with_id)
        return call_func_with_quib_values(self.func, args, kwargs)

    def _get_quibs_to_masks(self):
        """
        Get a mapping between quibs and a bool mask representing all the elements that are relevant to them in the
        result
        """
        quibs_mask = self._get_quib_ids_mask()
        return {quib: np.equal(quibs_mask, id(quib)) for quib in self._get_data_source_quibs()}

    def _get_quibs_to_indices_at_dimension(self, dimension: int, relevant_indices_mask) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to their referenced indices at a *specific dimension*
        """
        quibs_to_masks = self._get_quibs_to_masks()

        def replace_quib_with_index_at_dimension(q):
            return np.indices(q.get_shape() if isinstance(q, Quib) else np.shape(q))[dimension]

        args, kwargs = self._convert_data_sources_in_args(replace_quib_with_index_at_dimension)
        indices_res = call_func_with_quib_values(self._func, args, kwargs)

        return {
            quib: indices_res[np.logical_and(quibs_to_masks[quib], relevant_indices_mask)]
            for quib in self._get_data_source_quibs()
        }

    def get_quibs_to_indices_in_quibs(self, filtered_indices_in_result: Any) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after inversion of the
        indices relevant to the particular quib)
        """
        relevant_indices_mask = create_empty_array_with_values_at_indices(
            indices=filtered_indices_in_result,
            shape=self.get_shape(),
            value=True,
            empty_value=False
        )
        quibs = self._get_data_source_quibs()
        max_shape_length = max([quib.get_ndim() for quib in quibs]) if len(quibs) > 0 else 0
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

    def _backwards_translate_path(self, filtered_path_in_result: List[PathComponent]) \
            -> Dict[Quib, List[PathComponent]]:
        working_component = filtered_path_in_result[0].component if len(filtered_path_in_result) > 0 else True
        quibs_to_indices = self.get_quibs_to_indices_in_quibs(working_component)
        return {
            quib: [PathComponent(component=quibs_to_indices[quib], indexed_cls=np.ndarray)]
            if quibs_to_indices[quib] is not None else []
            for quib in quibs_to_indices
        }

    def _forward_translate_path(self, quib: Quib, path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        """
        There are two things we can potentially do:
        1. Translate the invalidation path given the current function quib (eg if this function quib is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        3. Pass on the current path to all our children
        """
        if len(path) > 0 and path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return [path]
        return super(TranspositionalFunctionQuib, self)._forward_translate_path(quib, path)

    def _tailored_forward_translate_indices(self, _quib: Quib, indices: Any) -> Any:
        if not (isinstance(indices, tuple) and len(indices) == self.get_ndim()):
            raise NotImplementedError()
        meta = self._function_metadata
        if not isinstance(meta, SupportedFunctionWithSimpleTranslation):
            raise NotImplementedError()
        return meta.forward_translate(indices, self)

    def _convert_data_sources_in_args(self, convert_data_source: Callable):
        """
        Return self.args and self.kwargs with all data source args converted with the given convert_data_source
        callback.
        """
        data_source_ids = set(map(id, self._get_data_source_args()))

        def _replace_arg_with_corresponding_mask_or_arg(_i, arg):
            if id(arg) in data_source_ids:
                return convert_data_source(arg)
            return arg

        return convert_args_and_kwargs(_replace_arg_with_corresponding_mask_or_arg, self.args, self.kwargs)

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

        def _convert_data_source(arg):
            if isinstance(arg, Quib):
                if arg is quib:
                    return self._get_source_shaped_bool_mask(arg, indices)
                else:
                    return np.full(arg.get_shape(), False)
            return np.full(np.shape(arg), False)

        args, kwargs = self._convert_data_sources_in_args(_convert_data_source)
        return call_func_with_quib_values(self.func, args, kwargs)

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
            for quib in self._get_data_source_quibs()
        }
