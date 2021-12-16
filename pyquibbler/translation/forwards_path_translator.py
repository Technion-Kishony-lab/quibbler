from abc import abstractmethod, ABC
from typing import Dict, Optional, Tuple

import numpy as np

from pyquibbler.translation.path_translator import Translator
from pyquibbler.translation.types import Source
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.assignment.assignment import working_component
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices


class ForwardsPathTranslator(Translator):

    def __init__(self, func_with_args_values, sources_to_paths: Dict[Source, Path], shape: Optional[Tuple[int, ...]]):
        super(ForwardsPathTranslator, self).__init__(func_with_args_values)
        self._sources_to_paths = sources_to_paths
        self._shape = shape

    @abstractmethod
    def translate(self) -> Dict[Source, Path]:
        pass
