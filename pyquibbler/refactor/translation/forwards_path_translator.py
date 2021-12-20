from abc import abstractmethod
from typing import Dict, Optional, Tuple, Type

from pyquibbler.refactor.translation.path_translator import Translator
from pyquibbler.refactor.translation.types import Source
from pyquibbler.quib.assignment import Path


class ForwardsPathTranslator(Translator):

    def __init__(self,
                 func_with_args_values, sources_to_paths: Dict[Source, Path],
                 shape: Optional[Tuple[int, ...]],
                 type_: Optional[Type]):
        super(ForwardsPathTranslator, self).__init__(func_with_args_values)
        self._sources_to_paths = sources_to_paths
        self._shape = shape
        self._type = type_

    @abstractmethod
    def translate(self) -> Dict[Source, Path]:
        pass
