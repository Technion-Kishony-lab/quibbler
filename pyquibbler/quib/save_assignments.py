from enum import Enum
from dataclasses import dataclass
from typing import Optional
from pyquibbler.exceptions import PyQuibblerException
import pathlib


class SaveFormat(str, Enum):

    TXT = 'txt'
    BIN = 'binary'
    VALUE_TXT = 'value_txt'


SAVEFORMAT_TO_FILE_EXT = {
    SaveFormat.BIN: '.quib',
    SaveFormat.TXT: '.txt',
    SaveFormat.VALUE_TXT: '.txt',
}


class ResponseToFileNotDefined(str, Enum):
    IGNORE = 0
    RAISE = 1
    WARNING = 2


@dataclass
class FileNotDefinedException(PyQuibblerException):

    quib_assigned_name: Optional[str]
    project_directory: Optional[pathlib.Path]

    def __str__(self):
        messages = []
        if self.quib_assigned_name is None:
            messages.append('set the assigned_name for the quib')
        if self.project_directory is None:
            messages.append('set a project directory (pyquibbler.set_project_directory)')
        return 'To save/load a quib you must ' + ' and '.join(messages) + '.'
