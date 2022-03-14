from functools import cached_property
from typing import Optional, Dict

import numpy as np

from pyquibbler.path.path_component import Path
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices
from pyquibbler.graphics.utils import remove_created_graphics
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.func_calling import QuibFuncCall
from pyquibbler.quib.func_calling.utils import cache_method_until_full_invalidation
from pyquibbler.quib.func_calling.func_calls.vectorize.utils import alter_signature, copy_vectorize, \
    get_indices_array, iter_arg_ids_and_values
from pyquibbler.quib.func_calling.func_calls.vectorize.vectorize_metadata \
    import VectorizeCall, VectorizeMetadata
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.specialized_functions.proxy import create_proxy
from pyquibbler.quib.utils.miscellaneous import copy_and_replace_quibs_with_vals
from pyquibbler.utils import convert_args_and_kwargs


class VectorizeQuibFuncCall(QuibFuncCall):

    def _wrap_vectorize_call_to_pass_quibs(self, call: VectorizeCall, args_metadata,
                                           results_core_ndims) -> VectorizeCall:
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
        return VectorizeCall(new_vectorize, args, kwargs, quibs_to_guard)

    def _get_vectorize_call(self, args_metadata, results_core_ndims, valid_path) -> VectorizeCall:
        """
        Get a VectorizeCall object to actually call vectorize with.
        If asked to pass quibs, return a modified call that passes quibs.
        """
        if self._call_func_with_quibs:
            (vectorize, *args), kwargs = self.args, self.kwargs
            call = VectorizeCall(vectorize, args, kwargs)
            call = self._wrap_vectorize_call_to_pass_quibs(call, args_metadata, results_core_ndims)
        else:
            quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
            new_args, new_kwargs = self.get_args_and_kwargs_valid_at_quibs_to_paths(quibs_to_paths)
            (vectorize, *args), kwargs = new_args, new_kwargs
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
        new_args, new_kwargs = self.get_args_and_kwargs_valid_at_quibs_to_paths(quibs_to_valid_paths={})
        (vectorize, *args), kwargs = new_args, new_kwargs
        return VectorizeCall(vectorize, args, kwargs).get_metadata(self._get_sample_result)

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

    def _wrap_vectorize_call_to_calc_only_needed(self, call: VectorizeCall, valid_path, otypes):
        """
        1. Create a bool mask with the same shape as the broadcast loop dimensions
        2. Create a wrapper for the pyfunc that receives the same arguments, and an additional boolean that
           instructs it to run the user function or return an empty result.
        3. Vectorize the wrapper and run it with the boolean mask in addition to the original arguments
        """
        valid_indices = True if len(valid_path) == 0 else valid_path[0].component
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
        return VectorizeCall(vectorize, (*args_to_add, *call.args), call.kwargs)

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

        call = self._get_vectorize_call(vectorize_metadata.args_metadata,
                                        vectorize_metadata.result_or_results_core_ndims, valid_path)
        call = self._wrap_vectorize_call_to_calc_only_needed(call, valid_path, vectorize_metadata.otypes)

        return call()
