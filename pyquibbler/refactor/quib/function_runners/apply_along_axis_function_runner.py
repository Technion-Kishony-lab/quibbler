from typing import Optional, Any, Callable, Tuple, Mapping, Set

import numpy as np
from numpy import ndindex, s_

from pyquibbler.quib import PathComponent, QuibGuard
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices
from pyquibbler.refactor.func_call import ArgsValues
from pyquibbler.refactor.graphics.graphics_collection import GraphicsCollection
from pyquibbler.refactor.graphics.utils import remove_created_graphics
from pyquibbler.refactor.quib.func_call_utils import get_func_call_with_quibs_valid_at_paths
from pyquibbler.refactor.quib.function_runners import FunctionRunner
from pyquibbler.refactor.quib.function_runners.utils import cache_method_until_full_invalidation
from pyquibbler.refactor.quib.quib import Quib


class ApplyAlongAxisFunctionRunner(FunctionRunner):

    def _run_func1d(self, arr: np.ndarray, *args, **kwargs) -> Any:
        """
        Run the one dimensional function on args and kwargs and potentially get value of the result if it's a quib
        """
        res = self.func1d(arr, *args, **kwargs)
        if isinstance(res, Quib):
            return res.get_value()
        return res

    # TODO: Move
    def get_args_values(self):
        return self.func_call.args_values

    @cache_method_until_full_invalidation
    def _get_sample_result(self) -> Any:
        """
        Get a result representing a possible return value of the user defined func1d.
        In practice, we simply run on index 0 of every dimension and take the oned slice.
        """
        input_array_shape = self.arr.get_shape()
        item = tuple([slice(None) if i == self.core_axis else 0 for i in range(len(input_array_shape))])

        if self.call_func_with_quibs:
            # TODO: Proxy quib!
            # input_array = ProxyQuib(self.arr)
            input_array = self.arr
            # raise Exception("Can't do this yet...")
        else:
            input_array = self.arr.get_value_valid_at_path([PathComponent(component=item, indexed_cls=np.ndarray)])

        oned_slice = input_array[item]
        func_call = get_func_call_with_quibs_valid_at_paths(self.func_call, quibs_to_valid_paths={})

        with remove_created_graphics():
            with external_call_failed_exception_handling():
                return self._run_func1d(
                    oned_slice,
                    *func_call.args_values.arg_values_by_name.get('args', []),
                    **func_call.args_values.arg_values_by_name.get('kwargs', {})
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
        from pyquibbler.refactor.user_utils import q
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
        if self.call_func_with_quibs:
            # TODO: Proxy quibs!
            return self.arr[indices]
            raise Exception("can't")
        return self.arr[indices].get_value()

    def _run_single_call(self, func: Callable,
                         graphics_collection: GraphicsCollection,
                         args: Tuple[Any, ...],
                         kwargs: Mapping[str, Any],
                         quibs_to_guard: Set[Quib]):
        """
        Run a single iteration of the function quib
        """
        # TODO: quibguard
        with graphics_collection.track_and_handle_new_graphics(
                kwargs_specified_in_artists_creation=set(self.kwargs.keys())
        ):
            ret_val = func(*args, **kwargs)

        # We don't allow returning quibs as results from functions
        from pyquibbler.refactor.quib.quib import Quib
        if isinstance(ret_val, Quib):
            ret_val = ret_val.get_value()

        return ret_val

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
                graphics_collection=self.graphics_collections[indices_before_axis + indices_after_axis],
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
        bool_mask = create_empty_array_with_values_at_indices(self.get_shape(),
                                                         indices=indices, value=True,
                                                         empty_value=False)
        for ii in ndindex(ni):
            for kk in ndindex(nk):
                out[ii + s_[(...,)] + kk] = self._get_result_at_indices(bool_mask,
                                                                        indices_before_axis=ii,
                                                                        indices_after_axis=kk,
                                                                        func1d_args=args_by_name.get('args', []),
                                                                        func1d_kwargs=args_by_name.get('kwargs', {}))

        return out

    @cache_method_until_full_invalidation
    def _get_loop_shape(self) -> Tuple[int, ...]:
        return tuple([s for i, s in enumerate(self.arr.get_shape()) if i != self.core_axis])

    def _run_on_path(self, valid_path: Optional[Path]):
        if valid_path is None:
            return self._get_invalid_value_at_correct_shape_and_dtype()

        return self._apply_along_axis(valid_path)
