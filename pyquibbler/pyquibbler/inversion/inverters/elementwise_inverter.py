from typing import Any, Type

import numpy as np

from pyquibbler.utilities.missing_value import missing
from pyquibbler.path import deep_get, Path
from pyquibbler.function_definitions import SourceLocation

from pyquibbler.translation import ForwardsPathTranslator, BackwardsPathTranslator
from pyquibbler.translation.types import Source
from pyquibbler.translation.utils import copy_and_replace_sources_with_vals
from pyquibbler.translation.translators.elementwise_translator import \
    BackwardsUnaryElementwisePathTranslator, ForwardsUnaryElementwisePathTranslator, \
    BackwardsBinaryElementwisePathTranslator, ForwardsBinaryElementwisePathTranslator

from .numpy_inverter import NumpyInverter
from ..inverter import Inverter


class BaseUnaryElementWiseInverter(Inverter):
    """ Base class for inversion that run an inverse function on each array element"""

    @property
    def inverse_func_requires_input(self):
        return self._func_call.func_definition.inverse_func_requires_input

    @property
    def inverse_func(self):
        return self._func_call.func_definition.inverse_func


class BaseBinaryElementWiseInverter(Inverter):
    """ Base class for inversion that run an inverse function on each array element"""

    @property
    def inverse_funcs(self):
        return self._func_call.func_definition.inverse_funcs


class BinaryElementwiseInverter(NumpyInverter, BaseBinaryElementWiseInverter):
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = BackwardsBinaryElementwisePathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = ForwardsBinaryElementwisePathTranslator

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:

        if any(location.argument.index == 0 for location in self._get_data_sources_to_locations().values()):
            # There is at least one source in the first (left) argument. So we invert to this argument.
            argument_to_invert_to = 0
            other_argument = 1
        else:
            argument_to_invert_to = 1
            other_argument = 0
        if source_location.argument.index != argument_to_invert_to:
            return missing

        inverse_func = self.inverse_funcs[argument_to_invert_to]

        other_argument_value = copy_and_replace_sources_with_vals(self._func_call.args[other_argument])
        other_argument_value = np.broadcast_to(other_argument_value, np.shape(self._previous_result))
        other_argument_value = deep_get(other_argument_value, path_in_result)
        return inverse_func(result_value, other_argument_value)


class UnaryElementwiseInverter(NumpyInverter, BaseUnaryElementWiseInverter):
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = BackwardsUnaryElementwisePathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = ForwardsUnaryElementwisePathTranslator

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:

        if self.inverse_func_requires_input:
            previous_input_value = deep_get(source.value, path_in_source)
            return self.inverse_func(result_value, previous_input_value)

        return self.inverse_func(result_value)
