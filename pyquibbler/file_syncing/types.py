from pyquibbler.utils import StrEnum
from dataclasses import dataclass
from typing import Optional
from pyquibbler.exceptions import PyQuibblerException
import pathlib


class SaveFormat(StrEnum):
    """
    Define the format for saving quib assignments:

    ``'off'``:  do not save

    ``'txt'``:  save assignments as text if possible (.txt)

    ``'bin'``:  save assignments as a binary file (.quib)

    ``'value_txt'``: for iquibs: save the value, rather than the assignments, as text (if possible).
    for fquibs: save assignments as text (if possible).

    ``'value_bin'``: for iquibs: save the value, rather than the assignments, as binary.
    for fquibs: save assignments as binary.

    See Also
    --------
    Quib.save_format, Project.save_format
    """

    OFF = 'off'
    TXT = 'txt'
    BIN = 'bin'
    VALUE_TXT = 'value_txt'
    VALUE_BIN = 'value_bin'


SAVE_FORMAT_TO_FILE_EXT = {
    SaveFormat.BIN: '.quib',
    SaveFormat.TXT: '.txt',
    SaveFormat.VALUE_TXT: '.txt',
    SaveFormat.VALUE_BIN: '.quib',
}


SAVE_FORMAT_TO_FQUIB_SAVE_FORMAT = {
    SaveFormat.OFF: SaveFormat.OFF,
    SaveFormat.TXT: SaveFormat.TXT,
    SaveFormat.BIN: SaveFormat.BIN,
    SaveFormat.VALUE_TXT: SaveFormat.TXT,
    SaveFormat.VALUE_BIN: SaveFormat.BIN,
}


class ResponseToFileNotDefined(StrEnum):
    IGNORE = 0
    RAISE = 1
    WARN = 2
    WARN_IF_DATA = 3


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
        return 'To save/load/sync a quib, you must ' + ' and '.join(messages) + '.'


class CannotSaveFunctionQuibsAsValueException(PyQuibblerException):

    def __str__(self):
        return "Saving as value is only allowed for iquibs."
