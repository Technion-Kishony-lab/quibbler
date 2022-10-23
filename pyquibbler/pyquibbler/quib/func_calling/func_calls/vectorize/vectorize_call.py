from functools import cached_property
from typing import Optional, Dict

import numpy as np

from pyquibbler import CacheMode
from pyquibbler.function_definitions import PositionalSourceLocation, FuncArgsKwargs, get_definition_for_function
from pyquibbler.quib.quib import Quib
from pyquibbler.path.path_component import Path, SpecialComponent, PathComponent
from pyquibbler.quib.utils.miscellaneous import copy_and_replace_quibs_with_vals
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.quib.func_calling.utils import cache_method_until_full_invalidation, convert_args_and_kwargs
from pyquibbler.quib.specialized_functions.proxy import create_proxy
from pyquibbler.function_definitions.types import iter_arg_ids_and_values, PositionalArgument
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices
from pyquibbler.graphics.utils import remove_created_graphics
from pyquibbler.utilities.missing_value import missing
from pyquibbler.utilities.numpy_original_functions import np_array

from .vectorize_metadata import VectorizeCaller, VectorizeMetadata
from .utils import alter_signature, copy_vectorize, get_indices_array


class VectorizeQuibFuncCall(CachedQuibFuncCall):

    def _wrap_vectorize_caller_to_pass_quibs(self, call: VectorizeCaller, args_metadata,
                                             results_core_ndims) -> VectorizeCaller:
        """
        Given a vectorize call and some metadata, return a new vectorize call that passes quibs to the vectorize pyfunc.
        This is done by wrapping the original pyfunc. The quibs in args and kwargs are replaced with
        indices arrays, and when the wrapper receives an index it uses it to get a GetItemQuib from the passed quib.
        """
        args_ids_and_values = list(iter_arg_ids_and_values(call.args, call.kwargs))

        non_excluded_quib_args = {arg_id: np.array(create_proxy(val)) for arg_id, val in args_ids_and_values
                                  if isinstance(val, Quib) and arg_id not in call.vectorize.excluded}
        excluded_quib_args = {arg_id: create_proxy(val) for arg_id, val in args_ids_and_values
                              if isinstance(val, Quib) and arg_id in call.vectorize.excluded}

        def convert_quibs_to_indices(arg_id, arg_val):
            if arg_id in non_excluded_quib_args:
                return get_indices_array(args_metadata[arg_id].loop_shape)
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
            alter_signature(args_metadata, results_core_ndims, {arg_id: 0 for arg_id in non_excluded_quib_args})

        def convert_indices_to_quibs(arg_id, arg_val):
            non_excluded_quib = non_excluded_quib_args.get(arg_id)
            if non_excluded_quib is not None:
                # We convert quibs to numpy arrays so we can slice them with tuples even if they are originally lists
                return non_excluded_quib[arg_val.indices]
            excluded_quib = excluded_quib_args.get(arg_id)
            if excluded_quib is not None:
                return excluded_quib
            return arg_val

        def wrapper(*args, **kwargs):
            args, kwargs = convert_args_and_kwargs(convert_indices_to_quibs, args, kwargs)
            result = call.vectorize.pyfunc(*args, **kwargs)
            return copy_and_replace_quibs_with_vals(result)

        quibs_to_guard = {*non_excluded_quib_args.values(), *excluded_quib_args.values()}
        new_vectorize = copy_vectorize(call.vectorize, func=wrapper, signature=signature)
        return VectorizeCaller(new_vectorize, args, kwargs, quibs_to_guard)

    def get_paths_for_sample_call(self, args_metadata) -> Dict[Quib, Path]:
        quibs_to_single_paths = {}
        for arg_id, arg_metadata in args_metadata.items():

            if isinstance(arg_id, int):
                arg_id += 1  # accounting for func at position 0

            arg = self.func_args_kwargs.get_arg_value_by_argument(arg_id)
            arg_sample_path = [PathComponent(arg_metadata.get_sample_component())]

            # we convert the `arg` path to paths of the sources within it using a np.array(arg) func_call:
            source_locations_in_arg = [
                PositionalSourceLocation(PositionalArgument(0), location.path)
                for location in self.data_source_locations if location.argument.get_arg_id() == arg_id]
            array_func_call = CachedQuibFuncCall(
                data_source_locations=source_locations_in_arg,
                parameter_source_locations=[],
                func_args_kwargs=FuncArgsKwargs(np_array, (arg,), {}),
                func_definition=get_definition_for_function(np_array),
                cache_mode=CacheMode.OFF,
            )
            current_arg_quibs_to_single_paths = array_func_call.backwards_translate_path(arg_sample_path)

            for quib, path in current_arg_quibs_to_single_paths.items():
                if quib in quibs_to_single_paths:
                    # TODO: in case the same quib source appears in different args, we need to take the union of the
                    #  two rquested paths. For now, we are taking the entire quib:
                    quibs_to_single_paths[quib] = []
                else:
                    quibs_to_single_paths[quib] = path

        return quibs_to_single_paths

    def _get_vectorize_caller(self, args_metadata, results_core_ndims, valid_path) -> VectorizeCaller:
        """
        Get a VectorizeCaller object to actually call vectorize with.
        If asked to pass quibs, return a modified call that passes quibs.
        """
        if self._pass_quibs:
            (vectorize, *args), kwargs = self.args, self.kwargs
            call = VectorizeCaller(vectorize, args, kwargs)
            call = self._wrap_vectorize_caller_to_pass_quibs(call, args_metadata, results_core_ndims)
        else:
            if valid_path is missing:
                quibs_to_paths = self.get_paths_for_sample_call(args_metadata)
            else:
                quibs_to_paths = self.backwards_translate_path(valid_path)
            new_args, new_kwargs = self._get_args_and_kwargs_valid_at_quibs_to_paths(quibs_to_paths)
            (vectorize, *args), kwargs = new_args, new_kwargs
            call = VectorizeCaller(vectorize, args, kwargs)
        return call

    def _get_sample_result(self, args_metadata, results_core_ndims):
        """
        Run the vectorized function on sample arguments to get s single sample result.
        Remove any graphics that were created during the call.
        """
        call = self._get_vectorize_caller(args_metadata, results_core_ndims, missing)
        with remove_created_graphics(), external_call_failed_exception_handling():
            return call.get_sample_result(args_metadata)

    @property
    @cache_method_until_full_invalidation
    def _vectorize_metadata(self) -> VectorizeMetadata:
        """
        Get and cache metadata for the vectorize call.
        """
        new_args, new_kwargs = self._get_args_and_kwargs_valid_at_quibs_to_paths(quibs_to_valid_paths={})
        (vectorize, *args), kwargs = new_args, new_kwargs
        return VectorizeCaller(vectorize, args, kwargs).get_metadata(self._get_sample_result)

    @cache_method_until_full_invalidation
    def _get_loop_shape(self):
        if self._vectorize_metadata.is_result_a_tuple:
            return ()
        return self._vectorize_metadata.result_loop_shape

    @cached_property
    def _vectorize(self) -> np.vectorize:
        """
        Get the vectorize object we were called with.
        """
        return self.args[0]

    def _wrap_vectorize_caller_to_calc_only_needed(self, call: VectorizeCaller, valid_path, otypes):
        """
        1. Create a bool mask with the same shape as the broadcast loop dimensions
        2. Create a wrapper for the pyfunc that receives the same arguments, and an additional boolean that
           instructs it to run the user function or return an empty result.
        3. Vectorize the wrapper and run it with the boolean mask in addition to the original arguments
        """
        valid_indices = SpecialComponent.ALL if len(valid_path) == 0 else valid_path[0].component
        bool_mask = create_bool_mask_with_true_at_indices(self.get_shape(), valid_indices)
        bool_mask = np.any(bool_mask, axis=self._vectorize_metadata.result_core_axes)
        # The logic in this wrapper should be as minimal as possible (including attribute access, etc.)
        # as it is run for every index in the loop.
        pyfunc = call.vectorize.pyfunc
        empty_result = np.empty(self._vectorize_metadata.result_core_shape, dtype=self._vectorize_metadata.result_dtype)

        def wrapper(graphics_collection, should_run, *args, **kwargs):
            if should_run:
                return self._run_single_call(func=pyfunc, args=args, kwargs=kwargs,
                                             graphics_collection=graphics_collection,
                                             quibs_allowed_to_access=call.quibs_to_guard)
            return empty_result

        args_to_add = (self.graphics_collections, bool_mask)
        wrapper_excluded = {i + len(args_to_add) if isinstance(i, int) else i for i in self._vectorize.excluded}
        wrapper_signature = call.vectorize.signature if call.vectorize.signature is None \
            else '(),' * len(args_to_add) + call.vectorize.signature
        vectorize = copy_vectorize(call.vectorize, func=wrapper, excluded=wrapper_excluded, signature=wrapper_signature,
                                   otypes=otypes)
        return VectorizeCaller(vectorize, (*args_to_add, *call.args), call.kwargs)

    @cache_method_until_full_invalidation
    def get_result_metadata(self) -> Dict:
        return {
            **super(VectorizeQuibFuncCall, self).get_result_metadata(),
            "vectorize_metadata": self._vectorize_metadata
        }

    def _run_on_path(self, valid_path: Optional[Path]):
        vectorize_metadata = self._vectorize_metadata
        if vectorize_metadata.is_result_a_tuple:
            return super()._run_on_path(valid_path)
        if valid_path is None:
            return np.zeros(vectorize_metadata.result_shape, dtype=vectorize_metadata.result_dtype)

        call = self._get_vectorize_caller(vectorize_metadata.args_metadata,
                                          vectorize_metadata.result_or_results_core_ndims, valid_path)
        call = self._wrap_vectorize_caller_to_calc_only_needed(call, valid_path, vectorize_metadata.otypes)

        return call()
