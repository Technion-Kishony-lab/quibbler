"""
Axiswise functions are functions that loop over an input array,
and perform a calculation on each sub-item.
The looping can be done on any combination of the dimensions of the input array.
The dimensions used for looping are called "loop dimensions", and the dimensions of the sub-items
passed to the underlying calculation are called "core dimensions".
In numpy terminology, when a function is applied "along an axis" or "over axes",
it means that those axes will be the core dimensions in the calculation.
For example, in the function np.sum(data, axis=x), x could be:
 - None: the core dimensions are ()
 - n (an integer): the core dimensions are (n,)
 - t (a tuple of integers): the core dimensions are t

In axiswise function, we could also separate the result ndarrays into loop dimensions and core dimensions.
The loop dimension would be n first dimensions, where n is the amount of loop dimensions used in the function.
The core dimensions would be the rest of the dimensions, which their amount is equal to the amount of dimensions
in the results of the inner calculation performed by the function.

When a specific index is invalidated in a data source of an axiswise function, the invalidation index in
the function result can be built by taking only the indexes in the loop dimensions.
"""
import numpy as np
from typing import Any

from pyquibbler.quib import Quib

from .graphics_function_quib import GraphicsFunctionQuib
from ..assignment.inverse_assignment.utils import create_empty_array_with_values_at_indices
from ..function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction


class AxisWiseGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.sum: SupportedFunction({0}),
        np.cumsum: SupportedFunction({0}),
        np.min: SupportedFunction({0}),
        np.max: SupportedFunction({0}),
        np.std: SupportedFunction({0}),
    }

    def _forward_translate_indices_to_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        source_bools = create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=invalidator_quib.get_shape().get_value()
        )
        kwargs = dict(axis=self._get_all_args_dict()['axis'], dtype=np.bool)
        for kwarg in ['keepdims', 'where']:
            if kwarg in self._get_all_args_dict(include_defaults=False):
                kwargs[kwarg] = self._get_all_args_dict()[kwarg]
        return np.logical_or.reduce(source_bools, **kwargs)
