from pyquibbler.utils import StrEnum
from dataclasses import dataclass
from typing import Optional
from pyquibbler.exceptions import PyQuibblerException
import pathlib


class SaveFormat(StrEnum):
    """
    Define the file format for saving quib assignments:

    See Also
    --------
    Quib.save_format, Project.save_format
    """

    OFF = 'off'
    "``'off'`` - do not save"

    TXT = 'txt'
    "``'txt'`` - save assignments as text if possible (.txt)"

    BIN = 'bin'
    "``'bin'`` - save assignments as a binary file (.quib)"


SAVE_FORMAT_TO_FILE_EXT = {
    SaveFormat.BIN: '.quib',
    SaveFormat.TXT: '.txt',
}


class ResponseToFileNotDefined(StrEnum):
    IGNORE = 0
    RAISE = 1
    WARN = 2
    WARN_IF_DATA = 3


@dataclass
class FileNotDefinedException(PyQuibblerException):
    """
    There are several reasons for a quib not having a defined file to save to.
    Here, we identify the specific reason.
    """
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
        return 'To save/load/sync a quib, you must ' + ' and '.join(messages) + '.'
