from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


class NothingToUndoException(PyQuibblerException):

    def __str__(self):
        return "There are no actions left to undo."


class NothingToRedoException(PyQuibblerException):

    def __str__(self):
        return "There are no actions left to redo."


@dataclass
class NoProjectDirectoryException(PyQuibblerException):
    action: str

    def __str__(self):
        return f"The project directory is not defined.\n" \
               f"To {self.action} quibs, set the project directory (see set_project_directory)."
