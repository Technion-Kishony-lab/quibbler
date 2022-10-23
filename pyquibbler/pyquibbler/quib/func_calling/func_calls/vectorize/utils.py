from __future__ import annotations
import numpy as np
from typing import Iterable, Optional, Dict, Union, TYPE_CHECKING
from string import ascii_letters
from itertools import islice

from pyquibbler.utilities.general_utils import Shape

if TYPE_CHECKING:
    from .vectorize_metadata import ArgsMetadata


def get_core_axes(core_ndim: int) -> Shape:
    """
    Return the numbers of the core axes given the amount of core dimensions.
    """
    return tuple(range(-1, -1 - core_ndim, -1))


def construct_core_dims_str(ndim: int, names: Iterable[str]) -> str:
    """
    Given an dimension amount and an iterable of usable dimension names,
    return a core dimension specification as used in a numpy ufunc signature.
    """
    return f'({",".join(islice(names, ndim))})'


def construct_signature(args_core_ndims: Iterable[int], results_core_ndims: Iterable[int]) -> str:
    """
    Create a numpy ufunc signature given args core ndims and results core ndims.
    """
    names = iter(ascii_letters)
    construct_core_dims_strs = lambda ndims: ",".join(construct_core_dims_str(ndim, names) for ndim in ndims)
    return f'{construct_core_dims_strs(args_core_ndims)}->{construct_core_dims_strs(results_core_ndims)}'


def alter_signature(args_metadata: ArgsMetadata, results_core_ndims: Iterable[int],
                    arg_ids_to_new_core_ndims: Optional[Dict[Union[str, int], int]]) -> str:
    """
    Create a new ufuc signature according the current args metadata, result core ndims,
    and a mapping between arg ids to their new core dimensions.
    """
    args_core_ndims = [arg_ids_to_new_core_ndims.pop(arg_id, arg_meta.core_ndim)
                       for arg_id, arg_meta in args_metadata.items()]
    assert not arg_ids_to_new_core_ndims, f'Invalid arg ids: {set(arg_ids_to_new_core_ndims.keys())}'
    return construct_signature(args_core_ndims, results_core_ndims)


def copy_vectorize(vectorize, func=None, otypes=None, excluded=None, signature=None) -> np.vectorize:
    """
    Copy a vectorize object while allowing to replace some attributes.
    """
    if func is None:
        func = vectorize.pyfunc
    if otypes is None:
        otypes = vectorize.otypes
    if excluded is None:
        excluded = vectorize.excluded
    if signature is None:
        signature = vectorize.signature
    return np.vectorize(func, otypes=otypes, doc=vectorize.__doc__, excluded=excluded, cache=vectorize.cache,
                        signature=signature, **vectorize.func_defintion_flags)


class Indices:
    """
    A small wrapper of indices, used to keep in an array without having core dimensions.
    """
    __slots__ = ['indices']

    def __init__(self, indices):
        self.indices = tuple(indices)


def get_indices_array(shape: Shape) -> np.ndarray:
    """
    Given a shape, return an ndarray in which each cell holds an Indices object with
    indices pointing to that cell.
    """
    return np.apply_along_axis(Indices, -1, np.moveaxis(np.indices(shape), 0, -1))
