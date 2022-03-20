from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Type


@dataclass
class PyQuibblerException(Exception, metaclass=ABCMeta):
    @abstractmethod
    def __str__(self):
        pass


@dataclass
class DebugException(PyQuibblerException):
    pass
