from __future__ import annotations
import numpy as np
from functools import partial
from typing import Tuple, Iterable, Optional, Dict, Union, Any, Callable
from string import ascii_letters
from itertools import islice, chain

from pyquibbler.quib.function_quibs.indices_translator_function_quib import Args, Kwargs

Shape = Tuple[int, ...]


def get_core_axes(core_ndim):
    return tuple(range(-1, -1 - core_ndim, -1))


def construct_core_dims_str(ndim: int, names: Iterable[str]) -> str:
    return f'({",".join(islice(names, ndim))})'


def iter_arg_ids_and_values(args, kwargs):
    return chain(enumerate(args), kwargs.items())


def construct_signature(core_ndims: Iterable[int], result_ndims: Iterable[int]) -> str:
    names = iter(ascii_letters)
    construct_core_dims_strs = lambda ndims: ",".join(construct_core_dims_str(ndim, names) for ndim in ndims)
    return f'{construct_core_dims_strs(core_ndims)}->{construct_core_dims_strs(result_ndims)}'


def alter_signature(args_metadata, results_core_ndims,
                    arg_ids_to_new_core_ndims: Optional[Dict[Union[str, int], int]]) -> str:
    assert results_core_ndims is not None  # TODO
    results_core_ndims = results_core_ndims if isinstance(results_core_ndims, list) else [results_core_ndims]  # TODO
    args_core_ndims = [arg_ids_to_new_core_ndims.pop(arg_id, arg_meta.core_ndim)
                       for arg_id, arg_meta in args_metadata.items()]
    assert not arg_ids_to_new_core_ndims, f'Invalid arg ids: {set(arg_ids_to_new_core_ndims.keys())}'
    return construct_signature(args_core_ndims, results_core_ndims)


def copy_vectorize(vectorize, func=None, otypes=None, excluded=None, signature=None) -> np.vectorize:
    if func is None:
        func = vectorize.pyfunc
    if otypes is None:
        otypes = vectorize.otypes
    if excluded is None:
        excluded = vectorize.excluded
    if signature is None:
        signature = vectorize.signature
    return np.vectorize(func, otypes=otypes, doc=vectorize.__doc__, excluded=excluded, cache=False,
                        signature=signature, pass_quibs=vectorize.pass_quibs)


class Indices:
    __slots__ = ['indices']

    def __init__(self, indices):
        self.indices = tuple(indices)


def get_indices_array(shape):
    return np.apply_along_axis(Indices, -1, np.moveaxis(np.indices(shape), 0, -1))


def get_sample_arg_core(args_metadata, arg_id: Union[str, int], arg_value: Any) -> Any:
    meta = args_metadata.get(arg_id)
    if meta is None:
        return arg_value
    # We should only use the loop shape and not the core shape, as the core shape changes with pass_quibs=True
    return np.asarray(arg_value)[(0,) * meta.loop_ndim]


def convert_args_and_kwargs(converter: Callable, args: Args, kwargs: Kwargs):
    return (tuple(converter(i, val) for i, val in enumerate(args)),
            {name: converter(name, val) for name, val in kwargs.items()})


def get_sample_result(vectorize, args, kwargs, args_metadata):
    args, kwargs = convert_args_and_kwargs(partial(get_sample_arg_core, args_metadata), args, kwargs)
    return vectorize.pyfunc(*args, **kwargs)
