from abc import ABCMeta, abstractmethod
from dataclasses import dataclass


@dataclass
class PyQuibblerException(Exception, metaclass=ABCMeta):
    @abstractmethod
    def __str__(self):
        pass


@dataclass
class DebugException(PyQuibblerException, metaclass=ABCMeta):
    pass
