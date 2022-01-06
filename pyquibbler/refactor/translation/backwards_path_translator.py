from abc import abstractmethod

from typing import Dict, Optional, Tuple, Type

from pyquibbler.refactor.translation.path_translator import PathTranslator
from pyquibbler.refactor.translation.types import Source
from pyquibbler.refactor.path.path_component import Path
from pyquibbler.refactor.path.utils import working_component


class BackwardsPathTranslator(PathTranslator):

    def __init__(self, func_call, shape: Optional[Tuple[int, ...]], type_: Optional[Type], path):
        super(BackwardsPathTranslator, self).__init__(func_call)
        self._shape = shape
        self._path = path
        self._type = type_

    @property
    def _working_component(self):
        return working_component(self._path)

    @abstractmethod
    def translate_in_order(self) -> Dict[Source, Path]:
        pass

    def translate_without_order(self) -> Dict[Source, Path]:
        return self.translate_in_order()
