from __future__ import annotations
import numpy as np
from typing import Tuple, Iterable
from string import ascii_letters
from itertools import islice

Shape = Tuple[int, ...]


def get_core_axes(core_ndim):
    return tuple(range(-1, -1 - core_ndim, -1))


def construct_core_dims_str(ndim: int, names: Iterable[str]) -> str:
    return f'({",".join(islice(names, ndim))})'


def construct_signature(core_ndims: Iterable[int], result_ndims: Iterable[int]) -> str:
    names = iter(ascii_letters)
    construct_core_dims_strs = lambda ndims: ",".join(construct_core_dims_str(ndim, names) for ndim in ndims)
    return f'{construct_core_dims_strs(core_ndims)}->{construct_core_dims_strs(result_ndims)}'


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
