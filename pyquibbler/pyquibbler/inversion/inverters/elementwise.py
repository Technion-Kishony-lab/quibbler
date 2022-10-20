import numpy as np

from abc import ABC

from typing import Any, Type

from pyquibbler.utilities.missing_value import missing
from pyquibbler.path import deep_get, Path
from pyquibbler.function_definitions import SourceLocation

from pyquibbler.quib.pretty_converters.operators import REVERSE_BINARY_FUNCS_TO_OPERATORS
from pyquibbler.function_overriding.third_party_overriding.numpy.inverse_functions import InverseFunc

from pyquibbler.path_translation import ForwardsPathTranslator, BackwardsPathTranslator
from pyquibbler.path_translation.types import Source
from pyquibbler.path_translation.utils import copy_and_replace_sources_with_vals
from pyquibbler.path_translation.translators.elementwise import \
    UnaryElementwiseBackwardsPathTranslator, UnaryElementwiseForwardsPathTranslator, \
    BinaryElementwiseBackwardsPathTranslator, BinaryElementwiseForwardsPathTranslator

from .numpy import NumpyInverter
from ..inverter import Inverter


class BaseUnaryElementWiseInverter(Inverter, ABC):
    """ Base class for inversion that run an inverse function on each array element"""

    def get_inverse_func_and_raise_if_none(self, argument_index) -> InverseFunc:
        inverse_func = self._func_call.func_definition.inverse_funcs[argument_index]
        if inverse_func is None:
            self._raise_run_failed_exception()
        return inverse_func


class BaseBinaryElementWiseInverter(BaseUnaryElementWiseInverter, ABC):
    """ Base class for inversion that run an inverse function on each array element"""

    @staticmethod
    def _switch_argument(argument_index):
        """
        Switch from the index of two arguments to the other
        """
        return 1 - argument_index

    def get_indices_of_argument_to_invert_to_and_of_other_argument(self):
        """
        Returns the index of the argument to which we invert, and the other argument.

        By definition, our default is the left (first) argument.
        But, if our quib is a reverse operator, then args have been switched. arg[1] is the default arg.
        """
        default_arg = 1 if self._func_call.func in REVERSE_BINARY_FUNCS_TO_OPERATORS else 0

        # If there is no quib in the default argument, then we switch to the other
        if any(location.argument.index == default_arg for location in self._get_data_sources_to_locations().values()):
            # There is at least one source in the default argument. So we invert to this argument.
            argument_to_invert_to = default_arg
        else:
            argument_to_invert_to = self._switch_argument(default_arg)

        other_argument = self._switch_argument(argument_to_invert_to)

        return argument_to_invert_to, other_argument


class BinaryElementwiseInverter(NumpyInverter, BaseBinaryElementWiseInverter):
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = BinaryElementwiseBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = BinaryElementwiseForwardsPathTranslator
    IS_ONE_TO_MANY_FUNC: bool = True  # because of broadcasting

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:

        argument_to_invert_to, other_argument = self.get_indices_of_argument_to_invert_to_and_of_other_argument()

        if source_location.argument.index != argument_to_invert_to:
            return missing

        inverse_func = self.get_inverse_func_and_raise_if_none(argument_to_invert_to)

        other_argument_value = copy_and_replace_sources_with_vals(self._func_call.args[other_argument])
        other_argument_value = np.broadcast_to(other_argument_value, np.shape(self._previous_result))
        other_argument_value = deep_get(other_argument_value, path_in_result)

        if inverse_func.requires_previous_input:
            previous_input_value = deep_get(source.value, path_in_source)
            return inverse_func.inv_func(result_value, other_argument_value, previous_input_value)

        return inverse_func.inv_func(result_value, other_argument_value)


class UnaryElementwiseInverter(NumpyInverter, BaseUnaryElementWiseInverter):
    BACKWARDS_TRANSLATOR_TYPE: Type[BackwardsPathTranslator] = UnaryElementwiseBackwardsPathTranslator
    FORWARDS_TRANSLATOR_TYPE: Type[ForwardsPathTranslator] = UnaryElementwiseForwardsPathTranslator
    IS_ONE_TO_MANY_FUNC: bool = False

    def _invert_value(self, source: Source, source_location: SourceLocation, path_in_source: Path,
                      result_value: Any, path_in_result: Path) -> Any:

        inverse_func = self.get_inverse_func_and_raise_if_none(0)

        if inverse_func.requires_previous_input:
            previous_input_value = deep_get(source.value, path_in_source)
            return inverse_func.inv_func(result_value, previous_input_value)

        return inverse_func.inv_func(result_value)
