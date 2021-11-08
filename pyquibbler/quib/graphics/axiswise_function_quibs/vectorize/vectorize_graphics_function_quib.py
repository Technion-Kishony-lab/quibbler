from __future__ import annotations
import numpy as np
from functools import cached_property
from typing import Any, Optional, List, Tuple, Set

from pyquibbler.quib.function_quibs.quib_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.quib import Quib, cache_method_until_full_invalidation
from pyquibbler.quib.proxy_quib import ProxyQuib
from pyquibbler.quib.graphics.graphics_function_quib import GraphicsFunctionQuib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, \
    SupportedFunction
from pyquibbler.quib.function_quibs.utils import ArgsValues
from pyquibbler.quib.utils import copy_and_replace_quibs_with_vals

from .utils import copy_vectorize, get_core_axes, get_indices_array, iter_arg_ids_and_values, alter_signature, \
    convert_args_and_kwargs
from .vectorize_metadata import VectorizeMetadata, ArgId, VectorizeCall
from ...utils import remove_created_graphics


def get_vectorize_call_data_args(args_values: ArgsValues) -> List[Any]:
    """
    Given a call to a vectorized function, return the arguments which act as data sources.
    We are using args_values.args and args_values.kwargs instead of the full args dict on purpose,
    to match vectorize function behavior.
    """
    vectorize, *args = args_values.args
    return [val for key, val in iter_arg_ids_and_values(args, args_values.kwargs) if key not in vectorize.excluded]


class VectorizeGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    A Quib for wrapping np.vectorize.__call__.
    Support forward and backwards translation, and partial calculation.
    """
    SUPPORTED_FUNCTIONS = {
        np.vectorize.__call__: SupportedFunction(get_vectorize_call_data_args)
    }

    @classmethod
    def _wrapper_call(cls, func, args, kwargs, **create_kwargs):
        """
        When create a quib function wrapper for np.vectorize.__call__, pass the QVectorize pass_quibs
        attribute as a kwargs to create().
        """
        return super()._wrapper_call(func, args, kwargs, **create_kwargs, pass_quibs=args[0].pass_quibs)

    @cached_property
    def _vectorize(self) -> np.vectorize:
        """
        Get the vectorize object we were called with.
        """
        return self.args[0]

    def _get_arg_ids_for_quib(self, quib: Quib) -> Set[ArgId]:
        """
        Given a parent quib, get all arg_ids it is given with.
        For example, in the call `f(q, x=q)`, `_get_arg_ids_for_quib(q)` will return `{0, 'x'}`
        """
        return {arg_id for arg_id, arg in iter_arg_ids_and_values(self.args[1:], self.kwargs) if quib is arg}

    def _wrap_vectorize_call_to_pass_quibs(self, call: VectorizeCall, args_metadata,
                                           results_core_ndims) -> VectorizeCall:
        """
        Given a vectorize call and some metadata, return a new vectorize call that passes quibs to the vectorize pyfunc.
        This is done by wrapping the original pyfunc. The quibs in args and kwargs are replaced with
        indices arrays, and when the wrapper receives an index it uses it to get a GetItemQuib from the passed quib.
        """
        # We convert quibs to numpy arrays so we can slice them with tuples even if they are originally lists
        quib_args = {arg_id: ProxyQuib(np.array(val)) for arg_id, val in iter_arg_ids_and_values(call.args, call.kwargs)
                     if isinstance(val, Quib) and arg_id not in call.vectorize.excluded}

        def convert_quibs_to_indices(arg_id, arg_val):
            if arg_id in quib_args:
                return get_indices_array(args_metadata[arg_id].loop_shape)
            elif isinstance(arg_val, Quib):
                return ProxyQuib(arg_val)
            return arg_val

        args, kwargs = convert_args_and_kwargs(convert_quibs_to_indices, call.args, call.kwargs)
        # Indices arrays have 0 core dimensions, so if the signature is None, it just stays None.
        # Otherwise, we need to construct a new signature in which the core dimensions of the quib
        # args are zero.
        # If indices core dimensions were one, then we couldn't keep using an empty signature when calling
        # vectorize - and that means we would have needed to call the original function to get the tuple
        # length - which is bad because we need to call it with quibs.
        # To solve that we make sure our core dimensions are always 0 by using the Indices class.
        signature = None if call.vectorize.signature is None else \
            alter_signature(args_metadata, results_core_ndims, {arg_id: 0 for arg_id in quib_args})

        def convert_indices_to_quibs(arg_id, arg_val):
            quib = quib_args.get(arg_id)
            if quib is None:
                return arg_val
            return quib[arg_val.indices]

        def wrapper(*args, **kwargs):
            args, kwargs = convert_args_and_kwargs(convert_indices_to_quibs, args, kwargs)
            result = call.vectorize.pyfunc(*args, **kwargs)
            return copy_and_replace_quibs_with_vals(result)

        return VectorizeCall(copy_vectorize(call.vectorize, func=wrapper, signature=signature), args, kwargs)

    def _get_vectorize_call(self, args_metadata, results_core_ndims, valid_path) -> VectorizeCall:
        """
        Get a VectorizeCall object to actually call vectorize with.
        If asked to pass quibs, return a modified call that passes quibs.
        """
        if self._pass_quibs:
            (vectorize, *args), kwargs = self.args, self.kwargs
            call = VectorizeCall(vectorize, args, kwargs)
            call = self._wrap_vectorize_call_to_pass_quibs(call, args_metadata, results_core_ndims)
        else:
            (vectorize, *args), kwargs = self._prepare_args_for_call(valid_path)
            call = VectorizeCall(vectorize, args, kwargs)
        return call

    def _get_sample_result(self, args_metadata, results_core_ndims):
        """
        Run the vectorized function on sample arguments to get s single sample result.
        Remove any graphics that were created during the call.
        """
        call = self._get_vectorize_call(args_metadata, results_core_ndims, None)
        with remove_created_graphics(), external_call_failed_exception_handling():
            return call.get_sample_result(args_metadata)

    @property
    @cache_method_until_full_invalidation
    def _vectorize_metadata(self) -> VectorizeMetadata:
        """
        Get and cache metadata for the vectorize call.
        """
        (vectorize, *args), kwargs = self._prepare_args_for_call(None)
        return VectorizeCall(vectorize, args, kwargs).get_metadata(self._get_sample_result)

    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        """
        Translate source bool mask to result bool mask by calling any on the source core dimensions,
        and broadcasting the result to the loop shape.
        """
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
        """
        Translate indices in result backwards to indices in a data source quib, by calling any on result
        core dimensions and de-broadcasting the loop dimensions into the argument loop dimension.
        """
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
        """
        Given a path in the result, return the path in the given quib on which the result path depends.
        """
        if len(filtered_path_in_result) == 0 or filtered_path_in_result[0].indexed_cls is tuple:
            return []
        working_component, *rest_of_path = filtered_path_in_result
        indices_in_data_source = self._backward_translate_indices_to_bool_mask(quib, working_component.component)
        return [PathComponent(self.get_type(), indices_in_data_source)]

    def _get_source_paths_of_quibs_given_path(self, filtered_path_in_result: List[PathComponent]):
        return {quib: self._get_source_path_in_quib(quib, filtered_path_in_result)
                for quib in self._get_data_source_quibs()}

    def _get_loop_shape(self) -> Tuple[int, ...]:
        if self._vectorize_metadata.is_result_a_tuple:
            return ()
        return self._vectorize_metadata.result_loop_shape

    def _wrap_vectorize_call_to_calc_only_needed(self, call: VectorizeCall, valid_path, otypes):
        """
        1. Create a bool mask with the same shape as the broadcast loop dimensions
        2. Create a wrapper for the pyfunc that receives the same arguments, and an additional boolean that
           instructs it to run the user function or return an empty result.
        3. Vectorize the wrapper and run it with the boolean mask in addition to the original arguments
        """
        valid_indices = True if len(valid_path) == 0 else valid_path[0].component
        bool_mask = np.any(self._get_bool_mask_representing_indices_in_result(valid_indices),
                           axis=self._vectorize_metadata.result_core_axes)
        # The logic in this wrapper should be as minimal as possible (including attribute access, etc.)
        # as it is run for every index in the loop.
        pyfunc = call.vectorize.pyfunc
        empty_result = np.zeros(self._vectorize_metadata.result_core_shape, dtype=self._vectorize_metadata.result_dtype)

        def wrapper(graphics_collection, should_run, *args, **kwargs):
            if should_run:
                with self._call_func_context(graphics_collection):
                    return pyfunc(*args, **kwargs)
            return empty_result

        args_to_add = (self._graphics_collection_ndarr, bool_mask)
        wrapper_excluded = {i + len(args_to_add) if isinstance(i, int) else i for i in self._vectorize.excluded}
        wrapper_signature = call.vectorize.signature if call.vectorize.signature is None \
            else '(),' * len(args_to_add) + call.vectorize.signature
        vectorize = copy_vectorize(call.vectorize, func=wrapper, excluded=wrapper_excluded, signature=wrapper_signature,
                                   otypes=otypes)
        return VectorizeCall(vectorize, (*args_to_add, *call.args), call.kwargs)

    def _call_func(self, valid_path: Optional[List[PathComponent]]):
        """
        Call vectoriz, but call the internal function only when required by the given valid_path.
        """
        self._initialize_graphics_ndarr()
        vectorize_metadata = self._vectorize_metadata
        if vectorize_metadata.is_result_a_tuple:
            return super()._call_func(valid_path)
        if valid_path is None:
            return np.zeros(vectorize_metadata.result_shape, dtype=vectorize_metadata.result_dtype)
        call = self._get_vectorize_call(vectorize_metadata.args_metadata,
                                        vectorize_metadata.result_or_results_core_ndims, valid_path)
        call = self._wrap_vectorize_call_to_calc_only_needed(call, valid_path, vectorize_metadata.otypes)

        with external_call_failed_exception_handling():
            return call()


class QVectorize(np.vectorize):
    """
    A small wrapper to the np.vectorize class, adding options to __init__ and wrapping __call__
    with a quib function wrapper.
    """

    def __init__(self, *args, pass_quibs=False, signature=None, cache=False, **kwargs):
        # We don't need the underlying vectorize object to cache, we are doing that ourselves.
        super().__init__(*args, signature=signature, cache=False, **kwargs)
        self.pass_quibs = pass_quibs

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.signature}>"
    __call__ = VectorizeGraphicsFunctionQuib.create_wrapper(np.vectorize.__call__)
