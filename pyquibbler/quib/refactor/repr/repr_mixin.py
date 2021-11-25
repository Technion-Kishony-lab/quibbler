from abc import ABC, abstractmethod
from typing import Union

from pyquibbler.logger import logger
from pyquibbler.quib.refactor.repr.pretty_converters import MathExpression


class ReprMixin(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def func(self):
        pass

    @property
    @abstractmethod
    def args(self):
        pass

    @property
    @abstractmethod
    def kwargs(self):
        pass

    def get_functional_representation_expression(self) -> Union[MathExpression, str]:
        from pyquibbler.quib.refactor.repr.pretty_converters import pretty_convert
        try:
            return pretty_convert.get_pretty_value_of_func_with_args_and_kwargs(self.func, self.args, self.kwargs)
        except Exception as e:
            logger.warning(f"Failed to get repr {e}")
            return "[exception during repr]"

    @property
    def functional_representation(self) -> str:
        """
        Get a string representing a functional representation of the quib.
        For example, in
        ```
        a = iquib(4)
        ```
        "iquib(4)" would be the functional representation
        """
        return str(self.get_functional_representation_expression())

    def pretty_repr(self):
        """
        Returns a pretty representation of the quib. Might calculate values of parent quibs.
        """
        return f"{self.name} = {self.functional_representation}" \
            if self.name is not None else self.functional_representation

    def __repr__(self):
        return f"<{self.__class__.__name__} - {self.func}"

    def __str__(self):
        return self.pretty_repr()
