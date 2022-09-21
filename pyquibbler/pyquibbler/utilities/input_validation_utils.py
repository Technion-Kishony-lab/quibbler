import functools
from dataclasses import dataclass
from typing import Type, Union, Tuple, Optional
from abc import ABC, abstractmethod

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utilities.basic_types import StrEnum


@dataclass
class InvalidArgumentException(PyQuibblerException, ABC):

    var_name: str

    def __str__(self):
        return f'Attribute {self.var_name} must be ' + self._must_be_message()

    @abstractmethod
    def _must_be_message(self):
        pass


@dataclass
class InvalidArgumentValueException(InvalidArgumentException):
    message: str = None

    def _must_be_message(self):
        return self.message


@dataclass
class InvalidArgumentTypeException(InvalidArgumentException):

    expected_type: Union[Type, Tuple[Type, ...]]

    def _must_be_message(self):
        types = self.expected_type if isinstance(self.expected_type, tuple) else (self.expected_type,)
        if len(types) == 1:
            return f'of type {types[0].__name__}'
        return f'of types {", ".join(map(lambda t: t.__name__, types))}'


def validate_user_input(**vars_to_expected_types):
    """
    Validate user input to ensure no arguments of unexpected types are given
    """
    def _decorator(func):

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            from pyquibbler.function_definitions.func_call import FuncArgsKwargs
            arg_values = FuncArgsKwargs(func, args, kwargs)
            for var_name, expected_types in vars_to_expected_types.items():
                if not isinstance(arg_values.get(var_name), expected_types):
                    raise InvalidArgumentTypeException(var_name=var_name, expected_type=expected_types)
            return func(*args, **kwargs)

        return _wrapper

    return _decorator


@dataclass
class UnknownEnumException(PyQuibblerException):
    attempted_value: str
    cls: Type[StrEnum]

    def __str__(self):
        return f"{self.attempted_value} is not a valid value for {self.cls}.\n" \
            f"Allowed values: {', '.join([value for value in self.cls])}"


def get_enum_by_str(cls: Type[StrEnum], value: Union[str, Type[StrEnum]], allow_none: bool = False) -> \
        Optional[StrEnum]:

    if type(value) is cls:
        return value
    if allow_none and value is None:
        return None
    if isinstance(value, str):
        try:
            return cls[value.upper()]
        except KeyError:
            pass
    raise UnknownEnumException(attempted_value=value, cls=cls) from None
