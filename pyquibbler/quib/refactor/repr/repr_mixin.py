from abc import ABC, abstractmethod


class ReprMixin(ABC):

    @property
    @abstractmethod
    def func(self):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} - {self.func}"

