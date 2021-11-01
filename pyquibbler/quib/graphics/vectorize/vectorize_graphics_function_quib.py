from __future__ import annotations
import numpy as np
from itertools import chain
from functools import cached_property
from typing import Any, Optional, List, Callable

from pyquibbler.quib.quib import Quib, cache_method_until_full_invalidation

from .vectorize_metadata import VectorizeMetadata, get_core_axes
from ..graphics_function_quib import GraphicsFunctionQuib
from ...assignment import PathComponent
from ...function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction
from ...function_quibs.utils import ArgsValues


class Indices:
    __slots__ = ['indices']

    def __init__(self, indices):
        self.indices = tuple(indices)


def iter_arg_ids_and_values(args, kwargs):
    return chain(enumerate(args), kwargs.items())


def get_vectorize_call_data_args(args_values: ArgsValues) -> List[Any]:
    """
    Given a call to a vectorized function, return the arguments which act as data sources.
    We are using args_values.args and args_values.kwargs instead of the full args dict on purpose,
    to match vectorize function behavior.
    """
    vectorize, *args = args_values.args
    return [val for key, val in iter_arg_ids_and_values(args, args_values.kwargs) if key not in vectorize.excluded]


def convert_args_and_kwargs(converter: Callable, args, kwargs):
    return ([converter(i, val) for i, val in enumerate(args)],
            {name: converter(name, val) for name, val in kwargs.items()})


class VectorizeGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    np.vectorize, without the signature parameter, turns normal python functions into elementwise functions.
    The signature parameter allows specifying the amount of core dimensions each argument has (and the result)
    and thereby turns the function into an axiswise function. When a vectorized function is called,
    the loop dimensions of all non-excluded arguments are broadcast together.
    The dimension of the result will be the broadcast loop dimension, plus the result core dimension specified
    in the signature, () by default.
    """
    SUPPORTED_FUNCTIONS = {
        np.vectorize.__call__: SupportedFunction(get_vectorize_call_data_args)
    }

    @cached_property
    def _vectorize(self) -> np.vectorize:
        """
        Get the vectorize object we were called with
        """
        return self.args[0]

    def _get_arg_ids_for_quib(self, quib: Quib):
        return {arg_id for arg_id, arg in iter_arg_ids_and_values(self.args[1:], self.kwargs) if quib is arg}

    @property
    @cache_method_until_full_invalidation
    def _vectorize_metadata(self) -> VectorizeMetadata:
        (vectorize, *args), kwargs = self._prepare_args_for_call(None)
        return VectorizeMetadata.from_vectorize_call(vectorize, args, kwargs)

    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        vectorize_metadata = self._vectorize_metadata
        source_bool_mask = self._get_source_shaped_bool_mask(invalidator_quib, indices)
        core_ndim = max(vectorize_metadata.args_metadata[arg_id].core_ndim
                        for arg_id in self._get_arg_ids_for_quib(invalidator_quib))
        source_bool_mask = np.any(source_bool_mask, axis=get_core_axes(core_ndim))
        return np.broadcast_to(source_bool_mask, vectorize_metadata.result_loop_shape)

    def _forward_translate_invalidation_path(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        working_component, *rest_of_path = path
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(invalidator_quib,
                                                                                 working_component.component)
        if not np.any(bool_mask_in_output_array):
            return []
        starting_path = [PathComponent(self.get_type(), bool_mask_in_output_array), *rest_of_path]

        vectorize_metadata = self._vectorize_metadata
        if vectorize_metadata.is_result_a_tuple:
            return [[PathComponent(tuple, i), *starting_path] for i in range(vectorize_metadata.tuple_length)]
        else:
            return [starting_path]

    def _backward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        vectorize_metadata = self._vectorize_metadata
        quib_arg_id = self._get_arg_ids_for_quib(quib).pop()
        quib_loop_shape = vectorize_metadata.args_metadata[quib_arg_id].loop_shape
        result_bool_mask = self._get_bool_mask_representing_indices_in_result(indices)
        result_core_axes = vectorize_metadata.result_core_axes
        new_broadcast_ndim = result_bool_mask.ndim - len(quib_loop_shape) - len(result_core_axes)
        assert new_broadcast_ndim >= 0
        new_broadcast_axes = tuple(range(0, new_broadcast_ndim))
        reduced_bool_mask = np.any(result_bool_mask, axis=result_core_axes + new_broadcast_axes)
        broadcast_loop_dimensions_to_reduce = tuple(i for i, (result_len, quib_len) in
                                                    enumerate(zip(reduced_bool_mask.shape, quib_loop_shape))
                                                    if result_len != quib_len)
        reduced_bool_mask = np.any(reduced_bool_mask, axis=broadcast_loop_dimensions_to_reduce, keepdims=True)
        return np.broadcast_to(reduced_bool_mask, quib_loop_shape)

    def _get_source_path_in_quib(self, quib: Quib, filtered_path_in_result: List[PathComponent]):
        if len(filtered_path_in_result) == 0 or filtered_path_in_result[0].indexed_cls is tuple:
            return []
        working_component, *rest_of_path = filtered_path_in_result
        indices_in_data_source = self._backward_translate_indices_to_bool_mask(quib, working_component.component)
        return [PathComponent(self.get_type(), indices_in_data_source)]

    def _get_source_paths_of_quibs_given_path(self, filtered_path_in_result: List[PathComponent]):
        return {quib: self._get_source_path_in_quib(quib, filtered_path_in_result)
                for quib in self._get_data_source_quibs()}

    def _copy_vectorize(self, vectorize, func=None, otypes=None, excluded=None, signature=None) -> np.vectorize:
        if func is None:
            func = vectorize.pyfunc
        if otypes is None:
            otypes = vectorize.otypes
        if excluded is None:
            excluded = vectorize.excluded
        if signature is None:
            signature = vectorize.signature
        return np.vectorize(func, otypes=otypes, doc=vectorize.__doc__, excluded=excluded, cache=False,
                            signature=signature, pass_quibs=vectorize.pass_quibs)

    def _wrap_vectorize_call_to_pass_quibs(self, vectorize_metadata: VectorizeMetadata) -> VectorizeMetadata:
        vectorize, args, kwargs = vectorize_metadata.vectorize, vectorize_metadata.args, vectorize_metadata.kwargs
        quib_args = {arg_id: val for arg_id, val in iter_arg_ids_and_values(self.args[1:], self.kwargs)
                     if isinstance(val, Quib)}

        def convert_quibs_to_indices(arg_id, arg_val):
            if arg_id in quib_args:
                indices = np.indices(vectorize_metadata.args_metadata[arg_id].loop_shape)
                return np.apply_along_axis(Indices, -1, np.moveaxis(indices, 0, -1))
            return arg_val

        args, kwargs = convert_args_and_kwargs(convert_quibs_to_indices, self.args[1:], self.kwargs)

        def convert_indices_to_quibs(arg_id, arg_val):
            quib = quib_args.get(arg_id)
            if quib is None:
                return arg_val
            return quib[arg_val.indices]

        def wrapper(*args, **kwargs):
            args, kwargs = convert_args_and_kwargs(convert_indices_to_quibs, args, kwargs)
            result = vectorize.pyfunc(*args, **kwargs)
            if isinstance(result, Quib):
                result = result.get_value()
            return result

        return VectorizeMetadata.from_vectorize_call(self._copy_vectorize(vectorize, func=wrapper), args, kwargs)

    def _wrap_vectorize_call_to_calc_only_needed(self, vectorize_metadata: VectorizeMetadata,
                                                 valid_path) -> VectorizeMetadata:
        """
        1. Create a bool mask with the same shape as the broadcast loop dimensions
        2. Create a wrapper for the pyfunc that receives the same arguments, and an additional boolean that
           instructs it to run the user function or return an empty result.
        3. Vectorize the wrapper and run it with the boolean mask in addition to the original arguments
        """
        vectorize, args, kwargs = vectorize_metadata.vectorize, vectorize_metadata.args, vectorize_metadata.kwargs
        bool_mask = np.any(self._get_bool_mask_representing_indices_in_result(valid_path[0].component),
                           axis=vectorize_metadata.result_core_axes)
        if not vectorize.pass_quibs:
            (_old_vectorize, *args), kwargs = self._prepare_args_for_call(valid_path)
        args = (bool_mask, *args)
        # The logic in this wrapper should be as minimal as possible (including attribute access, etc.)
        # as it is run for every index in the loop.
        pyfunc = vectorize.pyfunc
        empty_result = np.zeros(vectorize_metadata.result_core_shape, dtype=vectorize_metadata.result_dtype)
        wrapper = lambda should_run, *args, **kwargs: pyfunc(*args, **kwargs) if should_run else empty_result

        wrapper_excluded = {i + 1 if isinstance(i, int) else i for i in self._vectorize.excluded}
        wrapper_signature = vectorize.signature if vectorize.signature is None else '(),' + vectorize.signature
        vectorize = self._copy_vectorize(vectorize, func=wrapper, excluded=wrapper_excluded,
                                         signature=wrapper_signature)
        return VectorizeMetadata.from_vectorize_call(vectorize, args, kwargs)

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        vectorize_metadata = self._vectorize_metadata
        if self._vectorize.pass_quibs:
            vectorize_metadata = self._wrap_vectorize_call_to_pass_quibs(vectorize_metadata)
        if vectorize_metadata.is_result_a_tuple:
            return super()._call_func(valid_path)
        otypes = vectorize_metadata.otypes
        if valid_path is None:
            return np.zeros(vectorize_metadata.result_shape, dtype=vectorize_metadata.result_dtype)
        if len(valid_path) > 0:
            vectorize_metadata = self._wrap_vectorize_call_to_calc_only_needed(vectorize_metadata, valid_path)
        vectorize = self._copy_vectorize(vectorize_metadata.vectorize, otypes=otypes)
        return vectorize(*vectorize_metadata.args, **vectorize_metadata.kwargs)


class QVectorize(np.vectorize):
    def __init__(self, *args, pass_quibs=False, **kwargs):
        self.pass_quibs = pass_quibs
        super().__init__(*args, **kwargs)

    __call__ = VectorizeGraphicsFunctionQuib.create_wrapper(np.vectorize.__call__)
