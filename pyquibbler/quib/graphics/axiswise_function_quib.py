import numpy as np
from abc import abstractmethod
from typing import Any, Dict

from pyquibbler.quib.quib import Quib

from .graphics_function_quib import GraphicsFunctionQuib
from ..function_quibs.indices_translator_function_quib import IndicesTranslatorFunctionQuib, SupportedFunction


class AxisWiseGraphicsFunctionQuib(GraphicsFunctionQuib, IndicesTranslatorFunctionQuib):
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
    In reduction functions like min, max and sum, the loop dimensions will be the outer dimensions in the resulting array.
    In functions applied along an axis, like cumsum and apply_along_axis, the loop dimensions remains the same, but the core
    dimension is potentially expanded to multiple dimensions, depending on the calculation result dimensions.
    """
    SUPPORTED_KWARGS: Dict[str, str] = {}
    REQUIRED_KWARGS: Dict[str, str] = {}

    @abstractmethod
    def _call_forward_index_translator(self, kwargs, boolean_mask, invalidator_quib: Quib):
        """
        Do the actual forward index translation using a translator function with the given kwargs.
        """

    def _get_forward_index_translator_kwargs(self):
        """
        Prepare kwargs to call the translator function with according to self.SUPPORTED_KWARGS and self.REQUIRED_KWARGS.
        """
        kwargs = {}
        for original_kwarg_name, translator_kwarg_name in self.SUPPORTED_KWARGS.items():
            if original_kwarg_name in self._get_all_args_dict(include_defaults=False):
                kwargs[translator_kwarg_name] = self._get_all_args_dict(include_defaults=False)[original_kwarg_name]
        for original_kwarg_name, translator_kwarg_name in self.REQUIRED_KWARGS.items():
            kwargs[translator_kwarg_name] = self._get_all_args_dict(include_defaults=True)[original_kwarg_name]
        return kwargs

    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        source_bool_mask = self._get_source_shaped_bool_mask(quib, indices)
        kwargs = self._get_forward_index_translator_kwargs()
        return self._call_forward_index_translator(kwargs, source_bool_mask, quib)


class ReductionAxisWiseGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.sum: SupportedFunction({0}),
        np.min: SupportedFunction({0}),
        np.max: SupportedFunction({0}),
    }
    SUPPORTED_KWARGS = {'keepdims': 'keepdims', 'where': 'where'}
    REQUIRED_KWARGS = {'axis': 'axis'}

    def _call_forward_index_translator(self, kwargs, boolean_mask, invalidator_quib: Quib):
        """
        Calculate forward index translation for reduction functions by reducing the boolean arrays
        with the same reduction params.
        """
        return np.logical_or.reduce(boolean_mask, **kwargs)


class AlongAxisGraphicsFunctionQuib(AxisWiseGraphicsFunctionQuib):
    SUPPORTED_FUNCTIONS = {
        np.apply_along_axis: SupportedFunction({2}),
    }
    REQUIRED_KWARGS = {'axis': 'axis'}

    def _call_forward_index_translator(self, kwargs, boolean_mask, invalidator_quib: Quib):
        """
        Calculate forward index translation for apply_along_axis by applying np.any on the boolean mask.
        After that we expand and broadcast the reduced mask to match the actual result shape, which is dependent
        on the applied function return type.
        """
        result_shape = self.get_shape().get_value()
        func_result_ndim = len(result_shape) - len(invalidator_quib.get_shape().get_value()) + 1
        assert func_result_ndim >= 0, func_result_ndim
        axis = kwargs.pop('axis')
        applied = np.apply_along_axis(np.any, axis, boolean_mask, **kwargs)
        dims_to_expand = range(axis, axis + func_result_ndim) if axis >= 0 else \
            range(axis, axis - func_result_ndim, -1)
        expanded = np.expand_dims(applied, tuple(dims_to_expand))
        broadcast = np.broadcast_to(expanded, result_shape)
        return broadcast

