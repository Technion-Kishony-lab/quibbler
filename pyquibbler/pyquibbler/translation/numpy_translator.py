from abc import abstractmethod
from typing import Dict, Optional, Type, List

import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import Path, Paths, \
    PathComponent, deep_get
from pyquibbler.function_definitions import FuncCall, SourceLocation, FuncArgsKwargs
from pyquibbler.utilities.general_utils import Shape
from pyquibbler.utilities.numpy_original_functions import np_True

from .base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from pyquibbler.translation.numpy_translation_utils import convert_args_kwargs_to_source_index_codes
from .types import Source


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


class NewNumpyForwardsPathTranslator(ForwardsPathTranslator):
    """
    Basic logic for forward translating a path for numpy functions.
    Translates path of sources in data arguments to affected elements in the data arguments converted to numpy array.
    """

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

    def __init__(self,
                 func_call: FuncCall,
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Optional[Shape],
                 type_: Optional[Type]):
        super().__init__(func_call, source, source_location, path, shape, type_)

    @abstractmethod
    def forward_translate_masked_data_arguments_to_result_mask(self,
                                                               masked_func_args_kwargs: FuncArgsKwargs,
                                                               masked_data_arguments: List[NDArray[bool]]
                                                               ) -> NDArray[bool]:
        pass

    def _should_extract_element_out_of_array(self, within_source_array_path: Path) -> bool:
        return not isinstance(deep_get(np.array(self._source.value), within_source_array_path), np.ndarray)

    def forward_translate(self) -> Paths:

        masked_func_args_kwargs, remaining_path_to_source, within_source_array_path, within_source_element_path = \
            convert_args_kwargs_to_source_index_codes(self._func_call, self._source, self._source_location, self._path,
                                                      convert_to_bool_mask=True)

        masked_data_arguments = [
            masked_func_args_kwargs.get_arg_value_by_argument(argument) for
            argument in self._func_call.func_definition.get_data_source_arguments(self._func_call.func_args_kwargs)
        ]

        result_mask = \
            self.forward_translate_masked_data_arguments_to_result_mask(masked_func_args_kwargs, masked_data_arguments)

        if not np.any(result_mask):
            return []

        if result_mask is True or result_mask is np_True:
            within_target_array_path = []
        else:
            within_target_array_path = [PathComponent(result_mask, extract_element_out_of_array=False)]
        return [within_target_array_path + remaining_path_to_source + within_source_element_path]
