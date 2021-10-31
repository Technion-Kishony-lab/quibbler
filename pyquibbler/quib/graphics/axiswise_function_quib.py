import numpy as np
from dataclasses import dataclass
from itertools import chain
from functools import cached_property
from abc import abstractmethod
from typing import Any, Dict, Optional, List

from pyquibbler.quib.quib import Quib
from pyquibbler.quib.utils import copy_and_replace_quibs_with_vals

from .graphics_function_quib import GraphicsFunctionQuib
from ..assignment import PathComponent
from ..function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction
from ..function_quibs.utils import ArgsValues
from ..utils import iter_args_and_names_in_function_call


def get_vectorize_call_data_args(args_values: ArgsValues) -> List[Any]:
    """
    Given a call to a vectorized function, return the arguments which act as data sources.
    We are using args_values.args and args_values.kwargs instead of the full args dict on purpose,
    to match vectorize function behavior.
    """
    vectorize, *args = args_values.args
    return [val for key, val in chain(enumerate(args), args_values.kwargs.items()) if key not in vectorize.excluded]


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
    def _arg_values_in_wrapped_function(self):
        return list(dict(iter_args_and_names_in_function_call(self._vectorize.pyfunc,
                                                              self.args[1:], self.kwargs, False)).values())

    @cached_property
    def _vectorize(self) -> np.vectorize:
        """
        Get the vectorize object we were called with
        """
        return self.args[0]

    def _get_arg_core_ndim(self, arg: Any) -> int:
        """
        Return the core ndim of the argument in the given index.
        """
        arg_index = next(i for i, val in enumerate(self._arg_values_in_wrapped_function) if val is arg)
        if self._vectorize._in_and_out_core_dims is not None:
            return len(self._vectorize._in_and_out_core_dims[0][arg_index])
        return 0

    def _get_result_core_ndim(self):
        """
        Assuming the result is not a tuple, return the core ndim in the result.
        """
        if self._vectorize._in_and_out_core_dims is not None:
            out_core_dims = self._vectorize._in_and_out_core_dims[1]
            assert len(out_core_dims) == 1
            return len(out_core_dims[0])
        return 0

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
        args = [np.asarray(copy_and_replace_quibs_with_vals(arg)).flat[0] for arg in self.args[1:]]
        kwargs = {key: np.asarray(copy_and_replace_quibs_with_vals(val)).flat[0] for key, val in
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
        core_dims = self._get_arg_core_ndim(invalidator_quib)
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

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> Optional[List[PathComponent]]:
        if not self._is_quib_a_data_source(invalidator_quib):
            return [[]]
        invalidation_path = self._forward_translate_invalidation_path(invalidator_quib, path)
        tuple_len = self._get_tuple_output_len()
        if tuple_len is None:
            return [invalidation_path]
        else:
            return [[PathComponent(tuple, i), *invalidation_path] for i in range(tuple_len)]

    def _backward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        quib_loop_shape = quib.get_shape().get_value()[:-self._get_arg_core_ndim(quib) or None]
        result_bool_mask = self._get_bool_mask_representing_indices_in_result(indices)
        result_core_axes = tuple(range(-1, -1 - self._get_result_core_ndim(), -1))
        quib_result_loop_ndim_before_broadcast = result_bool_mask.ndim - len(quib_loop_shape) - len(result_core_axes)
        broadcast_loop_dimensions_to_remove = tuple(range(0, quib_result_loop_ndim_before_broadcast))
        reduced_bool_mask = np.any(result_bool_mask, axis=result_core_axes + broadcast_loop_dimensions_to_remove)
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
                for quib in self.get_data_source_quibs()}


@dataclass
class Arg:
    name: str

    def get_value(self, arg_dict: Dict[str, Any]) -> Any:
        return arg_dict[self.name]


@dataclass
class ArgWithDefault(Arg):
    default: Any

    def get_value(self, arg_dict: Dict[str, Any]) -> Any:
        return arg_dict.get(self.name, self.default)


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
    # Some numpy functions that allow not passing a keyword argument don't actually have a default value for it.
    # The default value is an instance of _NoValueType, and it is passed to an underlying function that
    # actually calculates the default value. In the future we could try and get the default value per
    # data type and function, but right now we assume we can know the default in advance.
    TRANSLATION_RELATED_ARGS: List[Arg]

    @abstractmethod
    def _forward_translate_bool_mask(self, args_dict, boolean_mask, invalidator_quib: Quib):
        """
        Do the actual forward index translation.
        """

    def _get_translation_related_arg_dict(self):
        arg_dict = {key: val for key, val in self._get_args_values(include_defaults=True).arg_values_by_name.items()
                    if not isinstance(val, np._globals._NoValueType)}
        return {arg.name: arg.get_value(arg_dict) for arg in self.TRANSLATION_RELATED_ARGS}

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        source_bool_mask = self._get_source_shaped_bool_mask(quib, indices)
        args_dict = self._get_translation_related_arg_dict()
        return self._forward_translate_bool_mask(args_dict, source_bool_mask, quib)

    @abstractmethod
    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        pass

    def _backward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        result_bool_mask = self._get_bool_mask_representing_indices_in_result(indices)
        args_dict = self._get_translation_related_arg_dict()
        return self._backward_translate_bool_mask(args_dict, result_bool_mask, quib)

    def _get_source_path_in_quib(self, quib: Quib, filtered_path_in_result: List[PathComponent]):
        if len(filtered_path_in_result) == 0:
            return []
        working_component, *rest_of_path = filtered_path_in_result
        indices_in_data_source = self._backward_translate_indices_to_bool_mask(quib, working_component.component)
        return [PathComponent(self.get_type(), indices_in_data_source)]

    def _get_source_paths_of_quibs_given_path(self, filtered_path_in_result: List[PathComponent]):
        return {quib: self._get_source_path_in_quib(quib, filtered_path_in_result)
                for quib in self.get_data_source_quibs()}


class ReductionAxisWiseGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.sum: SupportedFunction({0}),
        np.min: SupportedFunction({0}),
        np.amin: SupportedFunction({0}),
        np.max: SupportedFunction({0}),
        np.amax: SupportedFunction({0}),
        np.mean: SupportedFunction({0})
    }
    TRANSLATION_RELATED_ARGS = [Arg('axis'), ArgWithDefault('keepdims', False), ArgWithDefault('where', True)]

    def _forward_translate_bool_mask(self, args_dict, boolean_mask, invalidator_quib: Quib):
        """
        Calculate forward index translation for reduction functions by reducing the boolean arrays
        with the same reduction params.
        """
        return np.logical_or.reduce(boolean_mask, **args_dict)

    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        keepdims = args_dict['keepdims']
        if not keepdims:
            input_core_dims = args_dict['axis']
            if input_core_dims is not None:
                bool_mask = np.expand_dims(bool_mask, input_core_dims)
        bool_mask = np.broadcast_to(bool_mask, quib.get_shape().get_value())
        return np.logical_and(bool_mask, args_dict['where'])


class AlongAxisGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.apply_along_axis: SupportedFunction({2}),
    }
    TRANSLATION_RELATED_ARGS = [Arg('axis')]

    def _get_expanded_dims(self, axis, result_shape, source_shape):
        func_result_ndim = len(result_shape) - len(source_shape) + 1
        assert func_result_ndim >= 0, func_result_ndim
        return tuple(range(axis, axis + func_result_ndim) if axis >= 0 else
                     range(axis, axis - func_result_ndim, -1))

    def _forward_translate_bool_mask(self, args_dict, boolean_mask, invalidator_quib: Quib):
        """
        Calculate forward index translation for apply_along_axis by applying np.any on the boolean mask.
        After that we expand and broadcast the reduced mask to match the actual result shape, which is dependent
        on the applied function return type.
        """
        axis = args_dict.pop('axis')
        result_shape = self.get_shape().get_value()
        dims_to_expand = self._get_expanded_dims(axis, result_shape, invalidator_quib.get_shape().get_value())
        applied = np.apply_along_axis(np.any, axis, boolean_mask, **args_dict)
        expanded = np.expand_dims(applied, dims_to_expand)
        broadcast = np.broadcast_to(expanded, result_shape)
        return broadcast

    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape().get_value()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)
