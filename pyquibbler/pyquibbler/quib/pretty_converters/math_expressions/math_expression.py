from abc import ABC, abstractmethod

from pyquibbler.env import REPR_RETURNS_SHORT_NAME
from ..math_precedence import MathPrecedence


class MathExpression(ABC):
    def __str__(self):
        with REPR_RETURNS_SHORT_NAME.temporary_set(True):
            return self.get_str()

    def get_math_expression(self):
        return self

    @abstractmethod
    def get_str(self, with_spaces: bool = True):
        pass

    @property
    @abstractmethod
    def precedence(self) -> MathPrecedence:
        pass
