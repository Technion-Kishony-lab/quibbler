from typing import Optional, List, Any

import numpy as np

from pyquibbler.quib.proxy_quib import ProxyQuib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs.indices_translator_function_quib import SupportedFunction
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import AxisWiseGraphicsFunctionQuib, Arg
from pyquibbler.quib.quib import cache_method_until_full_invalidation


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

    @cache_method_until_full_invalidation
    def _get_empty_value_at_correct_shape_and_dtype(self):
        args_values = self._get_args_values()
        input_array = args_values['arr']
        # TODO: test when input array isn't quib
        input_array_shape = input_array.get_shape() if isinstance(input_array, Quib) else input_array.shape
        item = tuple([slice(0, None if i == self.looping_axis else 1) for i in range(len(input_array_shape))])
        minimized_array = input_array[item]

        # TODO: support pass quibs
        # TODO: support kwargs args
        res = self.func(func1d=args_values['func1d'], arr=minimized_array.get_value(), axis=self.looping_axis)

        # TODO: test ndarray returned
        # TODO: support returned quib
        expanded_shape = []
        for i in range(len(res.shape)):
            if i < self.looping_axis:
                expanded_shape.append(input_array_shape[i])
            elif self.looping_axis <= i < len(input_array_shape) - 1:
                expanded_shape.append(input_array_shape[i + 1])
            else:
                expanded_shape.append(res.shape[i])

        return np.broadcast_to(res, tuple(expanded_shape))

    @property
    def looping_axis(self):
        return self._get_args_values()['axis']

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        if valid_path is None:
            return self._get_empty_value_at_correct_shape_and_dtype()
        return super(AlongAxisGraphicsFunctionQuib, self)._call_func(valid_path)

    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)