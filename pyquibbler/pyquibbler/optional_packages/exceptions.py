from dataclasses import dataclass
from typing import List

from pyquibbler.exceptions import PyQuibblerException


@dataclass
class MissingPackagesForFunctionException(PyQuibblerException):
    function_name: str
    package_names: List[str]

    def __str__(self):
        return f'Using {self.function_name} requires installing the following packages:\n' \
               ', '.join(self.package_names)
