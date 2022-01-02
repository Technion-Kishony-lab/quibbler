import numpy as np
from typing import Optional, List, Any, Callable, Tuple, Mapping
from numpy import ndindex, s_
from pyquibbler.quib.function_quibs.external_call_failed_exception_handling \
    import external_call_failed_exception_handling
from pyquibbler.refactor.func_call import ArgsValues
from pyquibbler.quib.graphics.utils import remove_created_graphics
from pyquibbler.quib.proxy_quib import ProxyQuib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs.indices_translator_function_quib import SupportedFunction
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import AxisWiseGraphicsFunctionQuib, Arg
from pyquibbler.quib.quib import cache_method_until_full_invalidation


class ApplyAlongAxisGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.apply_along_axis: SupportedFunction({2}),
    }
    TRANSLATION_RELATED_ARGS = [Arg('axis')]

    _DEFAULT_EVALUATE_NOW = False

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, **init_kwargs):
        func_kwargs = func_kwargs or {}
        pass_quibs = func_kwargs.pop('pass_quibs', False)
        return super(ApplyAlongAxisGraphicsFunctionQuib, cls).create(func=func, func_args=func_args,
                                                                     cache_behavior=cache_behavior,
                                                                     func_kwargs=func_kwargs,
                                                                     pass_quibs=pass_quibs,
                                                                     **init_kwargs)

    def _get_expanded_dims(self, axis, result_shape, source_shape):
        func_result_ndim = len(result_shape) - len(source_shape) + 1
        assert func_result_ndim >= 0, func_result_ndim
        return tuple(range(axis, axis + func_result_ndim) if axis >= 0 else
                     range(axis, axis - func_result_ndim, -1))

    def _get_loop_shape(self) -> Tuple[int, ...]:
        return tuple([s for i, s in enumerate(self.arr.get_shape()) if i != self.core_axis])

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

    def _run_func1d(self, arr: np.ndarray, *args, **kwargs) -> Any:
        """
        Run the one dimensional function on args and kwargs and potentially get value of the result if it's a quib
        """
        res = self.func1d(arr, *args, **kwargs)
        if isinstance(res, Quib):
            return res.get_value()
        return res

    @cache_method_until_full_invalidation
    def _get_sample_result(self) -> Any:
        """
        Get a result representing a possible return value of the user defined func1d.
        In practice, we simply run on index 0 of every dimension and take the oned slice.
        """
        input_array_shape = self.arr.get_shape()
        item = tuple([slice(None) if i == self.core_axis else 0 for i in range(len(input_array_shape))])

        if self._pass_quibs:
            input_array = ProxyQuib(self.arr)
        else:
            input_array = self.arr.get_value_valid_at_path([PathComponent(component=item, indexed_cls=np.ndarray)])

        oned_slice = input_array[item]
        args, kwargs = self._prepare_args_for_call(None)
        args_values = ArgsValues.from_function_call(func=self.func, args=args, kwargs=kwargs, include_defaults=False)

        with remove_created_graphics():
            with external_call_failed_exception_handling():
                return self._run_func1d(
                    oned_slice,
                    *args_values.arg_values_by_name.get('args', []),
                    **args_values.arg_values_by_name.get('kwargs', {})
                )

    @cache_method_until_full_invalidation
    def _get_invalid_value_at_correct_shape_and_dtype(self) -> np.ndarray:
        """
        Get a value that represents the real result in both shape and dtype.
        Because the returned value can potentially be an ndarray, this will potentially execute the func1d once in
        order to get the results shape (but will remove any artists created by running it).
        """
        input_array_shape = self.arr.get_shape()
        sample_result_arr = np.asarray(self._get_sample_result())
        dims_to_expand = list(range(0, self.core_axis))
        dims_to_expand += list(range(-1, -(len(input_array_shape) - self.core_axis), -1))
        expanded = np.expand_dims(sample_result_arr, dims_to_expand)
        new_shape = [dim
                     for i, d in enumerate(input_array_shape)
                     for dim in ([d] if i != self.core_axis else sample_result_arr.shape)]
        return np.array(np.broadcast_to(expanded, new_shape))

    @property
    def core_axis(self) -> int:
        axis = self.get_args_values()['axis']
        if isinstance(axis, Quib):
            # since this is a parameter quib, we always need it completely valid in order to run anything
            axis = axis.get_value()
        return axis if axis >= 0 else len(self.arr.get_shape()) + axis

    @property
    def arr(self) -> Quib:
        from pyquibbler import q
        arr_ = self.get_args_values()['arr']
        # ensure we're dealing with an ndarray- because we're not always running apply_along_axis which takes care of
        # this for us (for example, when getting a sample result) we do this on any access to the array to ensure no
        # issues if we were passed a list
        return q(np.array, arr_)

    @property
    def func1d(self) -> Callable:
        return self.get_args_values()['func1d']

    def _get_oned_slice_for_running_func1d(self, indices: Tuple):
        """
        Get the proper slice as a parameter for the func- this depends on whether the user specified that he wants a
        quib representing the result (and if so, we create a proxy quib so as not to invalidate inner quibs he creates)
        or the values themselves of the slice
        """
        return ProxyQuib(self.arr[indices]) if self._pass_quibs else self.arr[indices].get_value()

    def _get_result_at_indices(self,
                               requested_indices_bool_mask: np.ndarray,
                               indices_before_axis: Tuple,
                               indices_after_axis: Tuple,
                               func1d_args: Tuple[Any, ...],
                               func1d_kwargs: Mapping[str, Any]):
        """
        Get a result at the indices given as arguments- this does not necessarily mean that func1d will be run; if the
        bool mask is not True within the given indices, then the result of this iteration was not requested (at
        valid_path), and so we will simply return the sample result as a placeholder
        """
        indices = indices_before_axis + s_[(...,)] + indices_after_axis
        if np.any(requested_indices_bool_mask[indices]):
            oned_slice = self._get_oned_slice_for_running_func1d(indices)
            res = self._run_single_call(
                func=self.func1d,
                graphics_collection=self._graphics_collection_ndarr[indices_before_axis + indices_after_axis],
                args=(oned_slice, *func1d_args),
                kwargs=func1d_kwargs,
                quibs_to_guard={oned_slice} if isinstance(oned_slice, Quib) else set()
            )
        else:
            res = self._get_sample_result()
        return res

    def _apply_along_axis(self, valid_path):
        """
        Run "apply_along_axis"- in reality, we need to map several different ndarrays, and so running apply_along_axis
        itself would be problematic (as we need the indices themselves of the 1d slice). Given this, we simply run on
        two loops of ndindex- the outer loop representing indices *before* the loop dimension, the inner loop
        representing indices *after* the loop dimension. We then select everything in between the two index tuples,
        which is a 1d slice.
        """
        indices = True if len(valid_path) == 0 else valid_path[0].component
        ni, nk = self.arr.get_shape()[:self.core_axis], self.arr.get_shape()[self.core_axis + 1:]
        out = self.get_value_valid_at_path(None)
        args_values = ArgsValues.from_function_call(func=self.func, args=self.args, kwargs=self.kwargs,
                                                    include_defaults=False)
        args_by_name = args_values.arg_values_by_name
        bool_mask = self._get_bool_mask_representing_indices_in_result(indices)
        for ii in ndindex(ni):
            for kk in ndindex(nk):
                out[ii + s_[(...,)] + kk] = self._get_result_at_indices(bool_mask,
                                                                        indices_before_axis=ii,
                                                                        indices_after_axis=kk,
                                                                        func1d_args=args_by_name.get('args', []),
                                                                        func1d_kwargs=args_by_name.get('kwargs', {}))

        return out

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        if valid_path is None:
            return self._get_invalid_value_at_correct_shape_and_dtype()

        self._initialize_graphics_collection_ndarr()
        return self._apply_along_axis(valid_path)

    def _backwards_translate_bool_mask(self, args_dict, bool_mask, quib: Quib):
        axis = args_dict.pop('axis')
        source_shape = quib.get_shape()
        expanded_dims = self._get_expanded_dims(axis, bool_mask.shape, source_shape)
        mask = np.expand_dims(np.any(bool_mask, axis=expanded_dims), axis)
        return np.broadcast_to(mask, source_shape)
