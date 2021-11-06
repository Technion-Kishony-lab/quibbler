from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from itertools import chain
from typing import Any, Dict, Optional, List, Tuple, Union, Callable

from pyquibbler.quib.function_quibs.indices_translator_function_quib import Args, Kwargs

from .utils import Shape, get_core_axes, get_sample_result

ArgId = Union[int, str]
ArgsMetadata: Dict[ArgId, VectorizeArgMetadata]


@dataclass
class VectorizeArgMetadata:
    shape: Shape
    core_shape: Shape
    loop_shape: Shape

    @classmethod
    def from_arg_and_core_ndim(cls, arg: Any, core_ndim: int) -> VectorizeArgMetadata:
        shape = np.shape(arg)
        assert len(shape) >= core_ndim
        if core_ndim == 0:
            return cls(shape, (), shape)
        return cls(shape, shape[-core_ndim:], shape[:-core_ndim])

    @property
    def core_ndim(self) -> int:
        return len(self.core_shape)

    @property
    def loop_ndim(self) -> int:
        return len(self.loop_shape)


@dataclass
class VectorizeMetadata:
    _get_sample_result: Callable

    args_metadata: ArgsMetadata
    result_loop_shape: Shape

    _is_result_a_tuple: Optional[bool]
    _results_core_ndims: Optional[List[int]]
    _result_dtypes: Optional[List[np.dtype]]
    _results_core_shapes: Optional[List[Shape]] = None

    def _run_sample_and_update_metadata(self):
        sample_result = self._get_sample_result(self.args_metadata, self._results_core_ndims)

        # update _is_result_a_tuple
        is_tuple = isinstance(sample_result, tuple)
        if self._is_result_a_tuple is None:
            self._is_result_a_tuple = is_tuple
        else:
            assert self._is_result_a_tuple == is_tuple

        # update _results_core_shapes
        assert self._results_core_shapes is None
        self._results_core_shapes = list(map(np.shape, sample_result)) if is_tuple else [np.shape(sample_result)]

        # update _results_core_ndims
        results_core_ndims = list(map(len, self._results_core_shapes))
        if self._results_core_ndims is None:
            self._results_core_ndims = results_core_ndims
        else:
            assert self._results_core_ndims == results_core_ndims

        # update _result_dtypes
        result_dtypes = [np.asarray(result).dtype for result in (sample_result if is_tuple else (sample_result,))]
        if self._result_dtypes is None:
            self._result_dtypes = result_dtypes
        else:
            assert self._result_dtypes == result_dtypes

    @property
    def is_result_a_tuple(self) -> bool:
        if self._is_result_a_tuple is None:
            self._run_sample_and_update_metadata()
        return self._is_result_a_tuple

    @property
    def results_core_ndims(self) -> List[int]:
        if self._results_core_ndims is None:
            self._run_sample_and_update_metadata()
        assert self._is_result_a_tuple is True
        return self._results_core_ndims

    @property
    def result_core_ndim(self) -> int:
        if self._results_core_ndims is None:
            self._run_sample_and_update_metadata()
        assert self._is_result_a_tuple is False
        return self._results_core_ndims[0]

    @property
    def result_or_results_core_ndims(self) -> List[int]:
        if self._results_core_ndims is None:
            self._run_sample_and_update_metadata()
        return self._results_core_ndims

    @property
    def result_core_axes(self) -> Tuple[int, ...]:
        return get_core_axes(self.result_core_ndim)

    @property
    def result_core_shape(self) -> Shape:
        if self.result_core_ndim == 0:
            return ()
        if self._results_core_shapes is None:
            self._run_sample_and_update_metadata()
        assert not self.is_result_a_tuple
        return self._results_core_shapes[0]

    @property
    def result_shape(self) -> Shape:
        return self.result_loop_shape + self.result_core_shape

    @property
    def result_dtype(self) -> np.dtype:
        if self._result_dtypes is None:
            self._run_sample_and_update_metadata()
        assert not self.is_result_a_tuple
        return self._result_dtypes[0]

    @property
    def result_dtypes(self) -> List[np.dtype]:
        if self._result_dtypes is None:
            self._run_sample_and_update_metadata()
        assert self.is_result_a_tuple
        return self._result_dtypes

    @property
    def otypes(self) -> str:
        if self._result_dtypes is None:
            self._run_sample_and_update_metadata()
        return ''.join(dtype.char for dtype in self._result_dtypes)

    @property
    def tuple_length(self):
        return len(self.result_dtypes)

    @classmethod
    def _get_args_and_results_core_ndims(cls, vectorize: np.vectorize, args: Args, kwargs: Kwargs):
        num_not_excluded = len((set(range(len(args))) | set(kwargs)) - vectorize.excluded)
        if vectorize._in_and_out_core_dims is None:
            args_core_ndims = [0] * num_not_excluded
            results_core_ndims = None
            is_tuple = None
        else:
            in_core_dims, out_core_dims = vectorize._in_and_out_core_dims
            args_core_ndims = list(map(len, in_core_dims))
            assert len(args_core_ndims) == num_not_excluded
            is_tuple = len(out_core_dims) > 1
            results_core_ndims = list(map(len, out_core_dims))
        return args_core_ndims, results_core_ndims, is_tuple

    @classmethod
    def _get_args_metadata(cls, vectorize, args: Args, kwargs: Kwargs, args_core_ndims):
        arg_index = 0
        args_metadata = {}
        for i, arg in chain(enumerate(args), kwargs.items()):
            if i not in vectorize.excluded:
                args_metadata[i] = VectorizeArgMetadata.from_arg_and_core_ndim(arg, args_core_ndims[arg_index])
                arg_index += 1
        assert arg_index == len(args_core_ndims)
        return args_metadata

    @classmethod
    def from_vectorize_call(cls, vectorize: np.vectorize, args: Args, kwargs: Kwargs, sample_result_callback=None):
        args_core_ndims, results_core_ndims, is_tuple = cls._get_args_and_results_core_ndims(vectorize, args, kwargs)
        args_metadata = cls._get_args_metadata(vectorize, args, kwargs, args_core_ndims)
        # Calculate the result shape like done in np.function_base._parse_input_dimensions
        dummy_arrays = [np.lib.stride_tricks.as_strided(0, arg_metadata.loop_shape)
                        for arg_metadata in args_metadata.values()]
        result_loop_shape = np.lib.stride_tricks._broadcast_shape(*dummy_arrays)
        result_dtypes = None if vectorize.otypes is None else list(map(np.dtype, vectorize.otypes))
        if sample_result_callback is None:
            sample_result_callback = lambda args_metadata, results_core_ndims: get_sample_result(vectorize, args,
                                                                                                 kwargs, args_metadata)
        return cls(sample_result_callback, args_metadata, result_loop_shape, is_tuple, results_core_ndims,
                   result_dtypes)
