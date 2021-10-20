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
The loop dimension would be n first dimensions, where n is the amount of loop dimensions used in the function.
The core dimensions would be the rest of the dimensions, which their amount is equal to the amount of dimensions
in the results of the inner calculation performed by the function.

When a specific index is invalidated in a data source of an axiswise function, the invalidation index in
the function result can be built by taking only the indexes in the loop dimensions.
"""
import numpy as np
from abc import abstractmethod
from typing import Any, Dict

from pyquibbler.quib.quib import Quib

from .graphics_function_quib import GraphicsFunctionQuib
from ..assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from ..function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction


class AxisWiseGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
    SUPPORTED_KWARGS: Dict[str, str] = {}
    REQUIRED_KWARGS: Dict[str, str] = {}

    def _get_source_shaped_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        return create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=invalidator_quib.get_shape().get_value()
        )

    @abstractmethod
    def _call_translator_func(self, kwargs, boolean_mask, invalidator_quib: Quib):
        pass

    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        source_bool_mask = self._get_source_shaped_bool_mask(invalidator_quib, indices)
        kwargs = {}
        for original_kwarg_name, translator_kwarg_name in self.SUPPORTED_KWARGS.items():
            if original_kwarg_name in self._get_all_args_dict(include_defaults=False):
                kwargs[translator_kwarg_name] = self._get_all_args_dict(include_defaults=False)[original_kwarg_name]
        for original_kwarg_name, translator_kwarg_name in self.REQUIRED_KWARGS.items():
            kwargs[translator_kwarg_name] = self._get_all_args_dict(include_defaults=True)[original_kwarg_name]
        return self._call_translator_func(kwargs, source_bool_mask, invalidator_quib)


class ReductionAxisWiseGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.sum: SupportedFunction({0}),
        np.min: SupportedFunction({0}),
        np.max: SupportedFunction({0}),
    }
    SUPPORTED_KWARGS = {'keepdims': 'keepdims', 'where': 'where'}
    REQUIRED_KWARGS = {'axis': 'axis'}

    def _call_translator_func(self, kwargs, boolean_mask, invalidator_quib: Quib):
        return np.logical_or.reduce(boolean_mask, **kwargs)


class AlongAxisGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.apply_along_axis: SupportedFunction({2}),
    }
    REQUIRED_KWARGS = {'axis': 'axis'}

    def _call_translator_func(self, kwargs, boolean_mask, invalidator_quib: Quib):
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
