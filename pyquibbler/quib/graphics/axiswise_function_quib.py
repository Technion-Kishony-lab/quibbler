import numpy as np
from itertools import chain
from functools import lru_cache, cached_property
from abc import abstractmethod
from typing import Any, Dict, Optional, List

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.utils import shallow_copy_and_replace_quibs_with_vals

from .graphics_function_quib import GraphicsFunctionQuib
from ..assignment import PathComponent
from ..function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction
from ..utils import iter_args_and_names_in_function_call


def get_vectorize_call_data_args(args, kwargs) -> List[Any]:
    """
    Given a call to a vectorized function, return the arguments which act as data sources.
    """
    vectorize, *args = args
    return [val for key, val in chain(enumerate(args), kwargs.items()) if key not in vectorize.excluded]


class VectorizeGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    np.vectorize, without the signature parameter, turns normal python functions into elementwise functions.
    The signature parameter allows specifying the amount of core dimensions each argument has (and the result)
    and thereby turns the function into an axiswise function. When a vectorized function is called,
    the loop dimensions of all non-excluded arguments are broadcast together.
    The dimension of the result will be the broadcast loop dimension, plus the result core dimension specified
    in the signature, () be default.
    """
    SUPPORTED_FUNCTIONS = {
        np.vectorize.__call__: SupportedFunction(get_vectorize_call_data_args)
    }

    @cached_property
    def _arg_values_in_wrapped_function(self):
        return list(dict(iter_args_and_names_in_function_call(self._vectorize.pyfunc,
                                                              self.args[1:], self.kwargs, False)).values())

    @cached_property
    def _vectorize(self) -> np.vectorize:
        """
        Get the vectorize object we were called with
        """
        return self.args[0]

    @lru_cache()
    def _get_arg_core_dims(self, arg_index: int) -> int:
        """
        Return the core dimensions of a given argument, which are 0 by default.
        """
        core_dims = 0
        in_and_out_core_dims = self._vectorize._in_and_out_core_dims
        if in_and_out_core_dims is not None:
            core_dims = len(in_and_out_core_dims[0][arg_index])
        return core_dims

    @property
    def _loop_shape(self):
        """
        Get the shape of the vectorize loop.
        This could also be done be broadcasting together the loop dimensions of all arguments.
        """
        if self._get_tuple_output_len():
            result_shape = self.get_value()[0].shape
        else:
            result_shape = self.get_shape().get_value()
        in_and_out_core_dims = self._vectorize._in_and_out_core_dims
        if in_and_out_core_dims is None:
            out_core_dims = 0
        else:
            out_core_dims = len(in_and_out_core_dims[1][0])
        return result_shape[:-out_core_dims] if out_core_dims else result_shape

    def _get_sample_elementwise_func_result(self):
        """
        Assuming no argument has core dimensions (and therefore the vectorized function must be elementwise),
        run the vectorized function on one set of arguments and return the result.
        """
        args = [np.asarray(shallow_copy_and_replace_quibs_with_vals(arg)).flat[0] for arg in self.args[1:]]
        kwargs = {key: np.asarray(shallow_copy_and_replace_quibs_with_vals(val)).flat[0] for key, val in
                  self.kwargs.items()}
        return self._vectorize.pyfunc(*args, **kwargs)

    def _get_tuple_output_len(self) -> Optional[int]:
        """
        If this vectorize function returns a tuple, return its length. Otherwise, return None.
        """
        in_and_out_core_dims = self._vectorize._in_and_out_core_dims
        if in_and_out_core_dims is not None:
            out_core_dims_len = len(in_and_out_core_dims[1])
            return None if out_core_dims_len == 1 else out_core_dims_len

        # If no signature is given, args core dimensions are all () so we can just flatten them.
        result = self._get_sample_elementwise_func_result()
        if isinstance(result, tuple):
            return len(result)
        return None

    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        source_bool_mask = self._get_source_shaped_bool_mask(invalidator_quib, indices)
        core_dims = self._get_arg_core_dims(self._arg_values_in_wrapped_function.index(invalidator_quib))
        if core_dims > 0:
            source_bool_mask = np.any(source_bool_mask, axis=tuple(range(source_bool_mask.ndim)[-core_dims:]))
        return np.broadcast_to(source_bool_mask, self._loop_shape)

    def _forward_translate_invalidation_path(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> Optional[List[PathComponent]]:
        working_component, *rest_of_path = path
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(invalidator_quib,
                                                                                 working_component.component)
        if np.any(bool_mask_in_output_array):
            return [PathComponent(self.get_type(), bool_mask_in_output_array), *rest_of_path]
        return None

    def _get_path_for_children_invalidation(self, invalidator_quib: Quib,
                                            path: List[PathComponent]) -> Optional[List[PathComponent]]:
        if not self._is_quib_a_data_source(invalidator_quib):
            return [[]]
        invalidation_path = self._forward_translate_invalidation_path(invalidator_quib, path)
        tuple_len = self._get_tuple_output_len()
        if tuple_len is None:
            return [invalidation_path]
        else:
            return [[PathComponent(tuple, i), *invalidation_path] for i in range(tuple_len)]

    def _invalidate_quib_with_children_at_path(self, invalidator_quib, path: List[PathComponent]):
        new_paths = self._get_path_for_children_invalidation(invalidator_quib, path) if path else [[]]
        if new_paths is not None:
            for new_path in new_paths:
                self._invalidate_self(new_path)
                self._invalidate_children_at_path(new_path)


class AxisWiseGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
    """
    Axiswise functions are functions that loop over an input array,
    and perform a calculation on each sub-item.
    The looping can be done on any combination of the dimensions of the input array.
    The dimensions used for looping are called "loop dimensions", and the dimensions of the sub-items
    passed to the underlying calculation are called "core dimensions".
    In numpy terminology, when a function is applied "along an axis" or "over axes",
    it means that those axes will be the core dimensions in the calculation.
    For example, in the function np.sum(data, axis=x), x could be:
     - None: the core dimensions are ()
     - n (an integer): the core dimensions are (n,)
     - t (a tuple of integers): the core dimensions are t

    In axiswise function, we could also separate the result ndarrays into loop dimensions and core dimensions.
    In reduction functions like min, max and sum, the loop dimensions will be the outer dimensions in the resulting
     array.
    In functions applied along an axis, like cumsum and apply_along_axis, the loop dimensions remains the same, but the
    core dimension is potentially expanded to multiple dimensions, depending on the calculation result dimensions.
    """
    SUPPORTED_KWARGS: Dict[str, str] = {}
    REQUIRED_KWARGS: Dict[str, str] = {}

    @abstractmethod
    def _call_forward_index_translator(self, kwargs, boolean_mask, invalidator_quib: Quib):
        """
        Do the actual forward index translation using a translator function with the given kwargs.
        """

    def _get_forward_index_translator_kwargs(self):
        """
        Prepare kwargs to call the translator function with according to self.SUPPORTED_KWARGS and self.REQUIRED_KWARGS.
        """
        kwargs = {}
        for original_kwarg_name, translator_kwarg_name in self.SUPPORTED_KWARGS.items():
            if original_kwarg_name in self._get_all_args_dict(include_defaults=False):
                kwargs[translator_kwarg_name] = self._get_all_args_dict(include_defaults=False)[original_kwarg_name]
        for original_kwarg_name, translator_kwarg_name in self.REQUIRED_KWARGS.items():
            kwargs[translator_kwarg_name] = self._get_all_args_dict(include_defaults=True)[original_kwarg_name]
        return kwargs

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        source_bool_mask = self._get_source_shaped_bool_mask(quib, indices)
        kwargs = self._get_forward_index_translator_kwargs()
        return self._call_forward_index_translator(kwargs, source_bool_mask, quib)


class ReductionAxisWiseGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.sum: SupportedFunction({0}),
        np.min: SupportedFunction({0}),
        np.amin: SupportedFunction({0}),
        np.max: SupportedFunction({0}),
        np.amax: SupportedFunction({0}),
    }
    SUPPORTED_KWARGS = {'keepdims': 'keepdims', 'where': 'where'}
    REQUIRED_KWARGS = {'axis': 'axis'}

    def _call_forward_index_translator(self, kwargs, boolean_mask, invalidator_quib: Quib):
        """
        Calculate forward index translation for reduction functions by reducing the boolean arrays
        with the same reduction params.
        """
        return np.logical_or.reduce(boolean_mask, **kwargs)


class AlongAxisGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.apply_along_axis: SupportedFunction({2}),
    }
    REQUIRED_KWARGS = {'axis': 'axis'}

    def _call_forward_index_translator(self, kwargs, boolean_mask, invalidator_quib: Quib):
        """
        Calculate forward index translation for apply_along_axis by applying np.any on the boolean mask.
        After that we expand and broadcast the reduced mask to match the actual result shape, which is dependent
        on the applied function return type.
        """
        result_shape = self.get_shape().get_value()
        func_result_ndim = len(result_shape) - len(invalidator_quib.get_shape().get_value()) + 1
        assert func_result_ndim >= 0, func_result_ndim
        axis = kwargs.pop('axis')
        applied = np.apply_along_axis(np.any, axis, boolean_mask, **kwargs)
        dims_to_expand = range(axis, axis + func_result_ndim) if axis >= 0 else \
            range(axis, axis - func_result_ndim, -1)
        expanded = np.expand_dims(applied, tuple(dims_to_expand))
        broadcast = np.broadcast_to(expanded, result_shape)
        return broadcast
