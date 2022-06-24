from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


class JupyerProjectException(PyQuibblerException):
    pass


@dataclass
class NoQuibFoundException(PyQuibblerException):
    quib_id: int

    def __str__(self):
        return f"No quib found with id {self.quib_id} - perhaps the quib was garbage disposed?"
