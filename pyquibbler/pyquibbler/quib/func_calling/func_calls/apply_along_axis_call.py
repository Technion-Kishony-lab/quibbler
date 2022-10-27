from typing import Optional, Any, Callable, Tuple

import numpy as np
from numpy import ndindex, s_

from pyquibbler.path import Path, PathComponent, SpecialComponent
from pyquibbler.quib.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.quib.specialized_functions.proxy import create_proxy
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices, Shape, Args, Kwargs
from pyquibbler.function_definitions.func_call import FuncArgsKwargs
from pyquibbler.graphics.utils import remove_created_graphics
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.quib.func_calling.utils import cache_method_until_full_invalidation
from pyquibbler.quib.quib import Quib
from pyquibbler.user_utils.quiby_funcs import q


class ApplyAlongAxisQuibFuncCall(CachedQuibFuncCall):

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
            input_array = create_proxy(self.arr)
        else:
            input_array = self.arr.get_value_valid_at_path([PathComponent(item)])

        oned_slice = input_array[item]
        new_args, new_kwargs = self._get_args_and_kwargs_valid_at_quibs_to_paths(quibs_to_valid_paths={})

        func_args_kwargs = FuncArgsKwargs(self.func, new_args, new_kwargs)

        with remove_created_graphics():
            with external_call_failed_exception_handling():
                return self._run_func1d(
                    oned_slice,
                    *func_args_kwargs.get('args', []),
                    **func_args_kwargs.get('kwargs', {}),

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
        axis = self.func_args_kwargs.get('axis')
        if isinstance(axis, Quib):
            # since this is a parameter quib, we always need it completely valid in order to run anything
            axis = axis.get_value()
        return axis if axis >= 0 else len(self.arr.get_shape()) + axis

    @property
    def arr(self) -> Quib:
        arr_ = self.func_args_kwargs.get('arr')
        # ensure we're dealing with an ndarray- because we're not always running apply_along_axis which takes care of
        # this for us (for example, when getting a sample result) we do this on any access to the array to ensure no
        # issues if we were passed a list
        return q(np.array, arr_)

    @property
    def func1d(self) -> Callable:
        return self.func_args_kwargs.get('func1d')

    def _get_oned_slice_for_running_func1d(self, indices: Tuple):
        """
        Get the proper slice as a parameter for the func- this depends on whether the user specified that he wants a
        quib representing the result (and if so, we create a proxy quib so as not to invalidate operators quibs
        he creates)
        or the values themselves of the slice
        """
        if self._pass_quibs:
            return create_proxy(self.arr[indices])
        path = [PathComponent(indices)]
        return self.arr.get_value_valid_at_path(path)[indices]

    def _get_result_at_indices(self,
                               requested_indices_bool_mask: np.ndarray,
                               indices_before_axis: Tuple,
                               indices_after_axis: Tuple,
                               func1d_args: Args,
                               func1d_kwargs: Kwargs):
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
                graphics_collection=self.graphics_collections[indices_before_axis + indices_after_axis],
                args=(oned_slice, *func1d_args),
                kwargs=func1d_kwargs,
                quibs_allowed_to_access={oned_slice} if isinstance(oned_slice, Quib) else set()
            )
        else:
            res = self._get_sample_result()
        return res

    def _apply_along_axis(self, valid_path):
        """
        Run "apply_along_axis"- in reality, we need to map several different ndarrays, and so running apply_along_axis
        itself would be problematic (as we need the indices themselves of the 1d slice). Given this, we simply run on
        two loops of ndindex- the outer loop representing indices *before* the loop dimension, the operators loop
        representing indices *after* the loop dimension. We then select everything in between the two index tuples,
        which is a 1d slice.
        """
        indices = SpecialComponent.ALL if len(valid_path) == 0 else valid_path[0].component
        ni, nk = self.arr.get_shape()[:self.core_axis], self.arr.get_shape()[self.core_axis + 1:]
        out = self.run([None])
        func_args_kwargs = FuncArgsKwargs(self.func, self.args, self.kwargs)
        args_by_name = func_args_kwargs.get_arg_values_by_keyword()
        bool_mask = create_bool_mask_with_true_at_indices(self.get_shape(), indices)
        for ii in ndindex(ni):
            for kk in ndindex(nk):
                out[ii + s_[(...,)] + kk] = self._get_result_at_indices(bool_mask,
                                                                        indices_before_axis=ii,
                                                                        indices_after_axis=kk,
                                                                        func1d_args=args_by_name.get('args', []),
                                                                        func1d_kwargs=args_by_name.get('kwargs', {}))

        return out

    @cache_method_until_full_invalidation
    def _get_loop_shape(self) -> Shape:
        return tuple([s for i, s in enumerate(self.arr.get_shape()) if i != self.core_axis])

    def _run_on_path(self, valid_path: Optional[Path]):
        if valid_path is None:
            return self._get_invalid_value_at_correct_shape_and_dtype()

        return self._apply_along_axis(valid_path)
