import functools
from dataclasses import dataclass
from typing import Type, Union, Tuple

from pyquibbler.exceptions import PyQuibblerException


@dataclass
class InvalidArgumentException(PyQuibblerException):

    var_name: str
    expected_type: Union[Type, Tuple[Type, ...]]

    def __str__(self):
        types = self.expected_type if isinstance(self.expected_type, tuple) else (self.expected_type,)
        return f'Argument {self.var_name} must be of types {", ".join(map(lambda t: t.__name__, types))}'


def validate_user_input(**vars_to_expected_types):
    """
    Validate user input to ensure no arguments of unexpected types are given
    """
    def _decorator(func):

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            from pyquibbler.refactor.function_definitions.func_call import ArgsValues
            arg_values = ArgsValues.from_function_call(func, args, kwargs, False)
            for var_name, expected_types in vars_to_expected_types.items():
                if not isinstance(arg_values[var_name], expected_types):
                    raise InvalidArgumentException(var_name=var_name, expected_type=expected_types)
            return func(*args, **kwargs)

        return _wrapper

    return _decorator
