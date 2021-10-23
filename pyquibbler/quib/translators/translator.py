from abc import ABCMeta, ABC, abstractmethod
from typing import Dict, List

from pyquibbler.quib import FunctionQuib, Quib
from pyquibbler.quib.assignment import PathComponent


class Translator(ABC):

    def __init__(self, function_quib: FunctionQuib):
        self._function_quib = function_quib

    @abstractmethod
    def get_quibs_to_paths_in_result(self) -> Dict[Quib, List[PathComponent]]:
        pass
