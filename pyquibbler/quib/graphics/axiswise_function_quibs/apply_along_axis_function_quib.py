from typing import Optional, List, Any, Callable

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.function_quibs.utils import ArgsValues
from pyquibbler.quib.proxy_quib import ProxyQuib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs.indices_translator_function_quib import SupportedFunction
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import AxisWiseGraphicsFunctionQuib, Arg
from pyquibbler.quib.quib import cache_method_until_full_invalidation
from pyquibbler.quib.utils import copy_and_replace_quibs_with_vals


class InputArrToApplyAlongAxisQuibMustBeQuibException(PyQuibblerException):
    pass


def get_shape(arr):
    if isinstance(arr, Quib):
        return arr.get_shape()
    return arr.shape


class AlongAxisGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.apply_along_axis: SupportedFunction({2}),
    }
    TRANSLATION_RELATED_ARGS = [Arg('axis')]

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, lazy=None, **init_kwargs):
        func_kwargs = func_kwargs or {}
        receive_quibs = func_kwargs.pop('pass_quibs', False)
        return super(AlongAxisGraphicsFunctionQuib, cls).create(func=func, func_args=func_args,
                                                                cache_behavior=cache_behavior,
                                                                lazy=lazy,
                                                                func_kwargs=func_kwargs,
                                                                receive_quibs=receive_quibs,
                                                                **init_kwargs)

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

    def _run_func1d(self, arr, *args, **kwargs):
        res = self.func1d(arr, *args, **kwargs)
        if isinstance(res, Quib):
            return res.get_value()
        return res

    @cache_method_until_full_invalidation
    def _get_sample_result(self):
        args_values = self._get_args_values()
        input_array = args_values['arr']
        input_array_shape = input_array.get_shape()
        item = tuple([slice(None) if i == self.looping_axis else 0 for i in range(len(input_array_shape))])
        input_array_value = input_array.get_value_valid_at_path([PathComponent(component=item,
                                                                               indexed_cls=input_array.get_type())])
        if not isinstance(input_array_value, np.ndarray):
            input_array_value = np.array(input_array_value)

        oned_slice = input_array_value[item]
        args, kwargs = self._prepare_args_for_call(None)
        args_values = ArgsValues.from_function_call(func=self.func, args=args, kwargs=kwargs, include_defaults=False)

        return copy_and_replace_quibs_with_vals(self._run_func1d(
             oned_slice,
             *args_values.arg_values_by_name.get('args', []),
             **args_values.arg_values_by_name.get('kwargs', {})
        ))

    @cache_method_until_full_invalidation
    def _get_empty_value_at_correct_shape_and_dtype(self):

        # TODO: support pass quibs

        input_array_shape = self.arr.get_shape()
        sample_result_arr = np.asarray(self._get_sample_result())
        positive_looping_axis = self.looping_axis if self.looping_axis >= 0 else len(input_array_shape) + \
                                                                                 self.looping_axis

        dims_to_expand = list(range(0, positive_looping_axis))
        dims_to_expand += list(range(-1, -(len(input_array_shape) - positive_looping_axis), -1))
        expanded = np.expand_dims(sample_result_arr, dims_to_expand)
        new_shape = [dim
                     for i, d in enumerate(input_array_shape)
                     for dim in ([d] if i != positive_looping_axis else sample_result_arr.shape)]
        return np.array(np.broadcast_to(expanded, new_shape))

    @property
    def looping_axis(self) -> int:
        axis = self._get_args_values()['axis']
        if isinstance(axis, Quib):
            # since this is a parameter quib, we always need it completely valid in order to run anything
            return axis.get_value()
        return axis

    @property
    def arr(self) -> Quib:
        arr_ = self._get_args_values()['arr']
        if not isinstance(arr_, Quib):
            raise InputArrToApplyAlongAxisQuibMustBeQuibException()
        return arr_

    @property
    def func1d(self) -> Callable:
        return self._get_args_values()['func1d']

    def _wrapped_func1d_call(self, arr, should_run_func_list, args=None, kwargs=None):
        if should_run_func_list.pop(0):
            return self._run_func1d(arr, *(args or []), **(kwargs or {}))
        return self._get_sample_result()

    def _run_with_pass_quibs(self):
        pass

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        if valid_path is None:
            return self._get_empty_value_at_correct_shape_and_dtype()

        self._initialize_artists_ndarr()  # TODO

        # Our underlying assumption is that apply_along_axis always runs in the same order
        # Therefore, we need to run the result bool mask backwards and then forwards through apply_along_axis in order
        # to get a list representing which function calls should go through and which should not
        indices = True if len(valid_path) == 0 else valid_path[0].component
        bool_mask = self._backward_translate_indices_to_bool_mask(indices=indices, quib=self.arr)
        func_calls = []
        np.apply_along_axis(lambda x: func_calls.append(np.any(x)), axis=self.looping_axis, arr=bool_mask)

        args, kwargs = self._prepare_args_for_call(valid_path)
        args_values = ArgsValues.from_function_call(func=self.func, args=args, kwargs=kwargs, include_defaults=False)
        values_by_name = args_values.arg_values_by_name
        values_by_name['func1d'] = self._wrapped_func1d_call
        values_by_name['should_run_func_list'] = func_calls

        if self._receive_quibs:
            # run yourself
            pass
        return self.func(**values_by_name)

    def _backward_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)
