from abc import abstractmethod
from typing import Dict, Optional, Type, List

import numpy as np
from numpy.typing import NDArray

from pyquibbler.path import translate_bool_vector_to_slice_if_possible, Path, Paths, \
    PathComponent, initial_path, deep_get
from pyquibbler.function_definitions import FuncCall, SourceLocation, FuncArgsKwargs
from pyquibbler.utilities.general_utils import Shape
from pyquibbler.utilities.numpy_original_functions import np_True

from .base_translators import BackwardsPathTranslator, ForwardsPathTranslator
from .exceptions import FailedToTranslateException
from pyquibbler.translation.numpy_translation_utils import convert_args_kwargs_to_source_index_codes
from .types import Source, NoMetadataSource


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


class OldNumpyForwardsPathTranslator(ForwardsPathTranslator):
    """
    Holds basic logic for how to forward translate a path for numpy functions- subclass this for any translator of a
    numpy function.
    """

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = True

    def __init__(self,
                 func_call: Type[FuncCall],
                 source: Source,
                 source_location: SourceLocation,
                 path: Path,
                 shape: Optional[Shape],
                 type_: Optional[Type]):
        super().__init__(func_call, source, source_location, path, shape, type_)

    @abstractmethod
    def forward_translate_initial_path_to_bool_mask(self, path: Path) -> np.ndarray:
        pass

    def forward_translate(self) -> Paths:

        path = self._path
        # TODO: THIS AUTO RETURNING OF [[]] IS INCORRECT IF PATH IS EMPTY, IN SOME EDGE CASES THIS DOESN'T HOLD
        if len(path) == 0:
            return [[]]

        if isinstance(self._source, NoMetadataSource):
            raise FailedToTranslateException()

        bool_mask_in_output_array = \
            self.forward_translate_initial_path_to_bool_mask(initial_path(path))
        if np.any(bool_mask_in_output_array):
            # If there exist both True's and False's in the boolean mask,
            # this function's quib result must be an ndarray- if it were a single item (say a PyObj, int, dict, list)
            # we'd expect it to be completely True (as it is ONE single object). If it is not a single item, it is by
            # definition an ndarray

            allowed_types = (np.ndarray, list, tuple)
            assert issubclass(self._type, allowed_types) or np.all(bool_mask_in_output_array)
            assert issubclass(self._type, allowed_types) or isinstance(bool_mask_in_output_array, np.bool_) \
                   or (bool_mask_in_output_array.shape == () and bool_mask_in_output_array.dtype == np.bool_)

            if not issubclass(self._type, allowed_types) and np.all(bool_mask_in_output_array):
                return [path[1:]]

            if len(path) > 0 and issubclass(self._source_type(), allowed_types):
                # If we are in a situation in which the first component is a referencing an ndarray or list, then the
                # `bool_mask_in_output_array` is already a combination of the first component with the
                # self._func_call.func- therefore, we are going to replace the first component with the
                # bool_mask_in_output_array
                rest_of_path = path[1:]
            else:
                rest_of_path = path

            if len(path) > 0 and issubclass(self._source_type(), (list, tuple)) \
                    and issubclass(self._type, (list, tuple)):
                assert np.ndim(bool_mask_in_output_array) == 1
                slice_index = translate_bool_vector_to_slice_if_possible(bool_mask_in_output_array)
                if slice_index:
                    return [[PathComponent(slice_index),
                             *rest_of_path]]
                return [[]]  # TODO: may need to treat as list of paths

            return [[PathComponent(bool_mask_in_output_array),
                     *rest_of_path]]

        return []


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
