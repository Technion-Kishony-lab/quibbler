from abc import ABC
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import Path, Paths
from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner
from pyquibbler.function_definitions import PositionalArgument, SourceLocation

from ..array_translation_utils import ArrayPathTranslator, run_func_call_with_new_args_kwargs
from ..types import Source
from ..utils import copy_and_replace_sources_with_vals
from ..array_index_codes import INDEX_TYPE

from .numpy import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator


def replace_list_with_object_array(arg):
    def _replace(obj):
        if isinstance(obj, list):
            # we add None and remove it to make sure we get a 1-dimensional array
            #  (this is ugly; I would love to hear of a better method)
            return np.array(obj + [None], dtype=object)[:-1]
        return obj

    if isinstance(arg, Source):
        arg = Source(value=_replace(arg.value))
    else:
        arg = _replace(arg)
    return arg


class ListOperatorPathTranslator(ConditionalRunner, ABC):
    """
    Takes care of translating list addition and multiplication.

    This is done by:
    (a) converting the list to object array
    (b) then using the numpy translator to convert to index code mask
    (c) convert the array of index code mask back to list
    (d) apply the operator function (add or mul)
    (e) convert the result back to array. indicating the affected indices

    List multiplication (like 4 * [1, 2, 3], or [1, 2, 3] * 4) is similar to list addition.
    Here, though, it is a biy tricky because both arguments are defined as data sources,
    but in practice, the scalar integer is not a data source, it is a parameter (if its value changes the size of
    the result changes). So we have to identify which one is the list and which is the integer and
    treat them differently.
    """

    def can_try(self) -> bool:
        # we know that we are an operator `+` or `*`, so just need to check that the result is a list
        return issubclass(self._type, list)

    def get_indices_of_data_args_which_are_lists(self):
        """
        Return a list of the indices (0, or 1) of args which refer to a list argument or to
        a quib that represents a list.
        """
        return [index for index, arg in enumerate(self._func_call.args)
                if isinstance(arg, list) or isinstance(arg, Source) and isinstance(arg.value, list)]

    def _get_result_mask(self, converter: ArrayPathTranslator):
        list_arg_indices = self.get_indices_of_data_args_which_are_lists()
        func_args_kwargs = converter.create_new_func_args_kwargs()
        for index in range(2):
            if index in list_arg_indices:
                # (a) convert the list data source to object array:
                is_focal_source = func_args_kwargs.args[index] is converter.focal_source
                func_args_kwargs.args[index] = replace_list_with_object_array(func_args_kwargs.args[index])
                if is_focal_source:
                    converter.focal_source = func_args_kwargs.args[index]

                # (b) do the numpy translator index code conversion
                converter.convert_a_data_argument(PositionalArgument(index))

                # (c) convert back to list
                func_args_kwargs.args[index] = func_args_kwargs.args[index].tolist()
            else:
                func_args_kwargs.args[index] = copy_and_replace_sources_with_vals(func_args_kwargs.args[index])

        # (d) apply the operator
        result = run_func_call_with_new_args_kwargs(self._func_call, func_args_kwargs)

        # (e) convert the resulted list of index codes (or True/False) to array
        return np.array(result)


class ListOperatorBackwardsPathTranslator(ListOperatorPathTranslator, NumpyBackwardsPathTranslator):

    def _get_source_path(self, source: Source, location: SourceLocation) -> Path:
        if location.argument.index not in self.get_indices_of_data_args_which_are_lists():
            return []
        return super()._get_source_path(source, location)

    def _get_indices_in_source(self,
                               data_argument_to_source_index_code_converter: ArrayPathTranslator,
                               result_bool_mask: NDArray[bool]) -> Tuple[NDArray[INDEX_TYPE], NDArray[bool]]:
        """
        We transform the indices of the source to the target by transferring the object arrays back to lists
        and applying the list addition/multiplication function.
        """
        result = self._get_result_mask(data_argument_to_source_index_code_converter)
        return result, result_bool_mask


class ListOperatorForwardsPathTranslator(ListOperatorPathTranslator, NumpyForwardsPathTranslator):

    def _forward_translate(self) -> Paths:
        if self._source_location.argument.index not in self.get_indices_of_data_args_which_are_lists():
            return [[]]
        return super()._forward_translate()

    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        We simply apply the quib function to the boolean-transformed arguments
        """
        result = self._get_result_mask(data_argument_to_mask_converter)
        return result
