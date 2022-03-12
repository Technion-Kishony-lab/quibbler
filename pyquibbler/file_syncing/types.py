from enum import Enum
from dataclasses import dataclass
from typing import Optional
from pyquibbler.exceptions import PyQuibblerException
import pathlib


class SaveFormat(str, Enum):

    OFF = 'off'
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
    actual_save_directory: Optional[pathlib.Path]
    actual_save_format: Optional[SaveFormat]

    def __str__(self):
        messages = []
        if self.quib_assigned_name is None:
            messages.append('set the assigned_name for the quib')
        if self.actual_save_directory is None:
            messages.append('set a project directory (pyquibbler.set_project_directory)')
        if self.actual_save_format == SaveFormat.OFF:
            messages.append('set the save_format')
        return 'To save/load a quib you must ' + ' and '.join(messages) + '.'
