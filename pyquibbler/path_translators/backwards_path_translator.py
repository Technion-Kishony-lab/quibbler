from abc import ABC, abstractmethod

from typing import Dict, Optional, Tuple

from pyquibbler.path_translators.path_translator import Translator
from pyquibbler.path_translators.types import Source
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.assignment.assignment import working_component


class BackwardsPathTranslator(Translator):

    def __init__(self, func_with_args_values, shape: Optional[Tuple[int, ...]], path):
        super(BackwardsPathTranslator, self).__init__(func_with_args_values)
        self._shape = shape
        self._path = path

    @property
    def _working_component(self):
        return working_component(self._path)

    @abstractmethod
    def translate(self) -> Dict[Source, Path]:
        pass
