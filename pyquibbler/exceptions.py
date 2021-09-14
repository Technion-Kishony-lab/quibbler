from dataclasses import dataclass


@dataclass
class PyQuibblerException(Exception):
    pass


@dataclass
class DebugException(PyQuibblerException):
    pass
