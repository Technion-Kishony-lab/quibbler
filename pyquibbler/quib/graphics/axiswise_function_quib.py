from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from abc import abstractmethod
from typing import Any, Dict, List

from pyquibbler.quib.quib import Quib

from .graphics_function_quib import GraphicsFunctionQuib
from ..assignment import PathComponent
from ..function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction


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
                for quib in self._get_data_source_quibs()}


class ReductionAxisWiseGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.sum: SupportedFunction({0}),
        np.min: SupportedFunction({0}),
        np.amin: SupportedFunction({0}),
        np.max: SupportedFunction({0}),
        np.amax: SupportedFunction({0}),
        np.mean: SupportedFunction({0}),
        np.average: SupportedFunction({0})
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
        bool_mask = np.broadcast_to(bool_mask, quib.get_shape())
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
        result_shape = self.get_shape()
        dims_to_expand = self._get_expanded_dims(axis, result_shape, invalidator_quib.get_shape())
        applied = np.apply_along_axis(np.any, axis, boolean_mask, **args_dict)
        expanded = np.expand_dims(applied, dims_to_expand)
        broadcast = np.broadcast_to(expanded, result_shape)
        return broadcast

    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)
