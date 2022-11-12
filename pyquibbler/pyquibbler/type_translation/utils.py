from dataclasses import dataclass
from typing import Type, Mapping

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utilities.missing_value import missing


@dataclass
class CannotFindRepresentativeValueForType(PyQuibblerException):
    type_: Type

    def __str__(self):
        return f"cannot find representative value for type {self._type}"


def get_representative_value_of_type(type_: Type):
    value = missing
    try:
        # important to start with scalar typing, because type(np.int64([])) is not np.int64
        value = type_(0)
    except TypeError:
        try:
            value = type_([])
        except TypeError:
            if issubclass(type_, Mapping):
                value = type_({})

    if type(value) is not type_:
        raise CannotFindRepresentativeValueForType(type_)

    return value
