from abc import abstractmethod
from typing import Dict, Optional, Type, List

import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import Path, Paths, \
    PathComponent, deep_get
from pyquibbler.function_definitions import SourceLocation, FuncArgsKwargs
from pyquibbler.utilities.numpy_original_functions import np_True

from pyquibbler.translation.base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from pyquibbler.translation.array_translation_utils import ArrayPathTranslator
from pyquibbler.translation.types import Source


class NumpyBackwardsPathTranslator(BackwardsPathTranslator):
    """
    Holds basic logic for how to backwards translate a path for numpy functions- subclass this for any translator of a
    numpy function.
    Mainly concerns surrounding logic with deep paths
    """

    @abstractmethod
    def _get_path_in_source(self, source: Source, location: SourceLocation):
        pass

    def _split_path(self):
        components_at_end = self._path[1:]
        current_components = self._path[0:1]
        if len(self._path) > 0 and self._path[0].referencing_field_in_field_array(self._type):
            components_at_end = [self._path[0], *components_at_end]
            current_components = []
        return current_components, components_at_end

    def backwards_translate(self) -> Dict[Source, Path]:
        sources_to_paths = {}
        working, rest = self._split_path()
        for source, location in zip(self._func_call.get_data_sources(), self._func_call.data_source_locations):
            new_path = self._get_path_in_source(source, location)
            if new_path is not None:
                sources_to_paths[source] = [*new_path, *rest]
        return sources_to_paths


class NumpyForwardsPathTranslator(ForwardsPathTranslator):
    """
    Basic logic for forward translating a path for numpy functions.
    Converts the data arguments to boolean arrays with indicating the affected elements in the source.

    sub-classes should encode the mapping from this boolean mask of the data arguments to a boolean mask the shape
    of the target, indicating affected elements in the target.
    """

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

    @abstractmethod
    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               data_argument_to_mask_converter: ArrayPathTranslator,
                                                               ) -> NDArray[bool]:
        """
        Forward translate boolean masks of the data sources (indicating the affected element)
        to a boolean mask of the function output.

        sub-methods can use either masked_data_arguments, which is a list containing the masks of the data arguments,
        or the masked_func_args_kwargs, where the data args have been replaced with their boolean masks.
        """
        pass

    def forward_translate(self) -> Paths:

        data_argument_to_mask_converter = \
            ArrayPathTranslator(func_call=self._func_call, focal_source=self._source,
                                focal_source_location=self._source_location, path_in_source=self._path,
                                convert_to_bool_mask=True)

        remaining_path_to_source = data_argument_to_mask_converter.get_path_from_array_element_to_source()
        within_source_element_path = data_argument_to_mask_converter.get_path_in_source_element()

        result_mask = \
            self.forward_translate_masked_data_arguments_to_result_mask(data_argument_to_mask_converter)

        if not np.any(result_mask):
            return []

        if result_mask is True or result_mask is np_True:
            within_target_array_path = []
        else:
            within_target_array_path = [PathComponent(result_mask, extract_element_out_of_array=False)]
        return [within_target_array_path + remaining_path_to_source + within_source_element_path]
