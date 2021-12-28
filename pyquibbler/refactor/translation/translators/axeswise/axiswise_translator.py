from abc import abstractmethod
from typing import Dict, List, Any

import numpy as np

from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import Arg
from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


class AxiswiseBackwardsTranslator(BackwardsPathTranslator):

    TRANSLATION_RELATED_ARGS: List[Arg]

    def _get_translation_related_arg_dict(self):
        arg_dict = {key: val for key, val in self._func_with_args_values.args_values.arg_values_by_name.items()
                    if not isinstance(val, np._globals._NoValueType)}
        return {arg.name: arg.get_value(arg_dict) for arg in self.TRANSLATION_RELATED_ARGS}

    @abstractmethod
    def _backwards_translate_bool_mask(self, source: Source, component: np.ndarray) -> np.ndarray:
        pass

    def _backwards_translate_indices_to_bool_mask(self, source: Source, indices: Any) -> Any:
        result_bool_mask = create_empty_array_with_values_at_indices(self._shape,
                                                                     indices=indices,
                                                                     value=True,
                                                                     empty_value=False)
        return self._backwards_translate_bool_mask(source, result_bool_mask)

    def _get_path_in_source(self, source: Source):
        if len(self._path) == 0:
            return []
        working_component, *rest_of_path = self._path
        indices_in_data_source = self._backwards_translate_indices_to_bool_mask(source,
                                                                                working_component.component)
        return [PathComponent(self._type, indices_in_data_source)]

    def translate_in_order(self) -> Dict[Source, Path]:
        return {source: self._get_path_in_source(source)
                for source in self.get_data_sources()}

