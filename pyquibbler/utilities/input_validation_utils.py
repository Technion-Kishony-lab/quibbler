import functools
from dataclasses import dataclass
from typing import Type, Union, Tuple
from abc import ABC, abstractmethod

from pyquibbler.exceptions import PyQuibblerException


@dataclass
class InvalidArgumentException(PyQuibblerException, ABC):

    var_name: str

    def __str__(self):
        return f'Argument {self.var_name} must be ' + self._must_be_message

    @abstractmethod
    def must_be_message(self):
        pass


@dataclass
class InvalidArgumentValueException(InvalidArgumentException):
    message: str = None

    def must_be_message(self):
        return self.message


@dataclass
class InvalidArgumentTypeException(InvalidArgumentException):

    expected_type: Union[Type, Tuple[Type, ...]]

    def must_be_message(self):
        types = self.expected_type if isinstance(self.expected_type, tuple) else (self.expected_type,)
        return f'of types {", ".join(map(lambda t: t.__name__, types))}'


def validate_user_input(**vars_to_expected_types):
    """
    Validate user input to ensure no arguments of unexpected types are given
    """
    def _decorator(func):

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            from pyquibbler.function_definitions.func_call import ArgsValues
            arg_values = ArgsValues.from_func_args_kwargs(func, args, kwargs, False)
            for var_name, expected_types in vars_to_expected_types.items():
                if not isinstance(arg_values[var_name], expected_types):
                    raise InvalidArgumentTypeException(var_name=var_name, expected_type=expected_types)
            return func(*args, **kwargs)

        return _wrapper

    return _decorator
