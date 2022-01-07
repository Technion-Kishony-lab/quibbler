from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any

import numpy as np

from pyquibbler.refactor.function_definitions.func_call import FuncCall
from pyquibbler.refactor.path import PathComponent
from pyquibbler.refactor.path import Path
from pyquibbler.refactor.path.utils import working_component
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.refactor.translation.numpy_translator import NumpyForwardsPathTranslator, NumpyBackwardsPathTranslator
from pyquibbler.refactor.utilities.general_utils import create_empty_array_with_values_at_indices
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


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
    arg_dict = {key: val for key, val in func_call.args_values.arg_values_by_name.items()
                if not isinstance(val, np._globals._NoValueType)}
    return {arg.name: arg.get_value(arg_dict) for arg in translation_related_args}


class AxiswiseBackwardsPathTranslator(NumpyBackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg]

    @abstractmethod
    def _backwards_translate_bool_mask(self, args_dict, source: Source, component: np.ndarray) -> np.ndarray:
        pass

    def _backwards_translate_indices_to_bool_mask(self, source: Source) -> Any:
        result_bool_mask = create_empty_array_with_values_at_indices(self._shape,
                                                                     indices=self._working_component,
                                                                     value=True,
                                                                     empty_value=False)
        args_dict = _get_translation_related_arg_dict(self._func_call, self.TRANSLATION_RELATED_ARGS)
        return self._backwards_translate_bool_mask(args_dict, source, result_bool_mask)

    def _get_path_in_source(self, source: Source):
        indices_in_data_source = self._backwards_translate_indices_to_bool_mask(source)
        return [PathComponent(self._type, indices_in_data_source)]


class AxiswiseForwardsPathTranslator(NumpyForwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg]

    @abstractmethod
    def _forward_translate_bool_mask(self, args_dict, boolean_mask, source: Source):
        pass

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        source_bool_mask = create_empty_array_with_values_at_indices(np.shape(source.value),
                                                                     indices=indices,
                                                                     value=True, empty_value=False)
        args_dict = _get_translation_related_arg_dict(self._func_call, self.TRANSLATION_RELATED_ARGS)
        return self._forward_translate_bool_mask(args_dict, source_bool_mask, source)

