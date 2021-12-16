from abc import ABC, abstractmethod

from typing import Dict, Optional, Tuple, Type

from pyquibbler.translation.path_translator import Translator
from pyquibbler.translation.types import Source
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.assignment.assignment import working_component


class BackwardsPathTranslator(Translator):

    SUPPORTING_FUNCS = NotImplemented
    PRIORITY = 0

    def __init__(self, func_with_args_values, shape: Optional[Tuple[int, ...]], type_: Optional[Type], path):
        super(BackwardsPathTranslator, self).__init__(func_with_args_values)
        self._shape = shape
        self._path = path
        self._type = type_

    @property
    def _working_component(self):
        return working_component(self._path)

    @abstractmethod
    def translate(self) -> Dict[Source, Path]:
        pass
