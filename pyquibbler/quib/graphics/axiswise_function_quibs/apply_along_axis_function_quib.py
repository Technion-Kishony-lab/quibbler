from typing import Optional, List, Any

import numpy as np

from pyquibbler.quib.proxy_quib import ProxyQuib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs.indices_translator_function_quib import SupportedFunction
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import AxisWiseGraphicsFunctionQuib, Arg
from pyquibbler.quib.quib import cache_method_until_full_invalidation


def get_shape(arr):
    if isinstance(arr, Quib):
        return arr.get_shape()
    return arr.shape

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
    def _get_sample_result(self):
        args_values = self._get_args_values()
        input_array = args_values['arr']
        # TODO: test when input array isn't quib
        input_array_shape = input_array.get_shape()
        item = tuple([slice(None) if i == self.looping_axis else 0 for i in range(len(input_array_shape))])
        minimized_array = input_array[item]
        return self.func1d(minimized_array.get_value())

    @cache_method_until_full_invalidation
    def _get_empty_value_at_correct_shape_and_dtype(self):

        # TODO: support pass quibs
        # TODO: support kwargs args

        arr = np.asarray(self._get_sample_result())
        input_array_shape = self.arr.get_shape()
        expanded = arr[tuple([np.newaxis for r in range(len(self.arr.get_shape()) - 1)])]

        # TODO: test ndarray returned
        # TODO: support returned quib
        expanded_shape = []
        for i in range(len(expanded.shape)):
            if i < self.looping_axis:
                expanded_shape.append(input_array_shape[i])
            elif self.looping_axis <= i < len(input_array_shape) - 1:
                expanded_shape.append(input_array_shape[i + 1])
            else:
                expanded_shape.append(expanded.shape[i])

        return np.array(np.broadcast_to(expanded, tuple(expanded_shape)))

    @property
    def looping_axis(self):
        return self._get_args_values()['axis']

    @property
    def arr(self):
        return self._get_args_values()['arr']

    @property
    def func1d(self):
        return self._get_args_values()['func1d']

    def _wrapped_func1d_call(self, arr, should_run_func_list, *args, **kwargs):
        if should_run_func_list.pop(0):
            self.func1d(arr, *args, **kwargs)
        return self._get_sample_result()

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        if valid_path is None:
            return self._get_empty_value_at_correct_shape_and_dtype()
        elif len(valid_path) == 0:
            return super(AlongAxisGraphicsFunctionQuib, self)._call_func(valid_path)

        self._initialize_artists_ndarr()  # TODO
        # Our underlying assumption is that apply_along_axis always runs in the same order
        # Therefore, we need to run the result bool mask backwards and then forwards through apply_along_axis in order
        # to get a list representing which function calls should go through and which should not
        bool_mask = self._backward_translate_indices_to_bool_mask(indices=valid_path[0].component, quib=self.arr)
        func_calls = []
        np.apply_along_axis(lambda x: func_calls.append(np.any(x)), axis=self.looping_axis, arr=bool_mask)

        return self.func(self._wrapped_func1d_call,
                         axis=self.looping_axis,
                         arr=self.arr.get_value(),
                         should_run_func_list=func_calls)

    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)
