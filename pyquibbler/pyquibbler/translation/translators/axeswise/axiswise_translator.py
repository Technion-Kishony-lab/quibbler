from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any

import numpy as np

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.path import PathComponent
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices

from ...types import Source
from ...numpy_translator import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator


@dataclass
class Arg:
    name: str

    def get_value(self, arg_dict: Dict[str, Any]) -> Any:
        return arg_dict[self.name]


@dataclass
class ArgWithDefault(Arg):
    default: Any

    def get_value(self, arg_dict: Dict[str, Any]) -> Any:
        return arg_dict.get(self.name, self.default)


def _get_translation_related_arg_dict(func_call: FuncCall, translation_related_args: List[Arg]):
    arg_dict = {key: val for key, val in func_call.func_args_kwargs.get_arg_values_by_name().items()
                if not isinstance(val, np._globals._NoValueType)}
    return {arg.name: arg.get_value(arg_dict) for arg in translation_related_args}


class AxiswiseBackwardsPathTranslator(NumpyBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg]

    @abstractmethod
    def _backwards_translate_bool_mask(self, args_dict, source: Source, component: np.ndarray) -> np.ndarray:
        pass

    def _backwards_translate_indices_to_bool_mask(self, source: Source) -> Any:
        result_bool_mask = create_bool_mask_with_true_at_indices(self._shape, self._working_component)
        args_dict = _get_translation_related_arg_dict(self._func_call, self.TRANSLATION_RELATED_ARGS)
        return self._backwards_translate_bool_mask(args_dict, source, result_bool_mask)

    def _get_path_in_source(self, source: Source, location: SourceLocation):
        working_path, _ = self._split_path()
        if len(working_path) == 0:
            return []
        indices_in_data_source = self._backwards_translate_indices_to_bool_mask(source)
        return [PathComponent(indices_in_data_source)]


class AxiswiseForwardsPathTranslator(NumpyForwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg]

    @abstractmethod
    def _forward_translate_bool_mask(self, args_dict, boolean_mask, source: Source):
        pass

    def _forward_translate_indices_to_bool_mask(self, indices: Any):
        source_bool_mask = create_bool_mask_with_true_at_indices(np.shape(self._source.value), indices)
        args_dict = _get_translation_related_arg_dict(self._func_call, self.TRANSLATION_RELATED_ARGS)
        return self._forward_translate_bool_mask(args_dict, source_bool_mask, self._source)
