from dataclasses import dataclass
from abc import ABC, abstractmethod
import os
from enum import Enum
import pathlib
from typing import Optional

from pyquibbler.debug_utils.logger import logger

"""
This file follows the logic of file-syncing from MatQuibbler
"""


class FileStatus(Enum):
    UNCHECKED = 0
    MISSING = 1
    EXISTS = 2


class FileComparison(Enum):
    SAME_FILE = 0,  # the file existed and did not change
    CHANGED = 1,  # the file existed and changed
    DELETED = 2,  # a file was deleted
    CREATED = 3,  # a file was created
    NO_FILE = 4,  # file did not exist and still does not exist
    FILE_FOUND = 5,  # the file was found upon initiation
    FILE_NOT_FOUND = 6,  # the file was not found upon initiation


FILE_STATUSES_TO_FILECOMPARISON = {
    (FileStatus.EXISTS, FileStatus.EXISTS, True): FileComparison.SAME_FILE,
    (FileStatus.EXISTS, FileStatus.EXISTS, False): FileComparison.CHANGED,
    (FileStatus.EXISTS, FileStatus.MISSING, False): FileComparison.DELETED,
    (FileStatus.MISSING, FileStatus.EXISTS, False): FileComparison.CREATED,
    (FileStatus.MISSING, FileStatus.MISSING, True): FileComparison.NO_FILE,
    (FileStatus.UNCHECKED, FileStatus.MISSING, False): FileComparison.FILE_NOT_FOUND,
    (FileStatus.UNCHECKED, FileStatus.EXISTS, False): FileComparison.FILE_FOUND,
}


class SaveLoadAction(Enum):
    NOTHING = 0  # do nothing. do not even propose
    NONE = 1  # do nothing
    SAVE = 2  # save to file
    DELETE = 3  # delete the file
    LOAD = 4  # load date from file
    CLEAR = 5  # clear the data

    def is_action(self):
        return self._value_ >= 2


@dataclass
class ActionVerification:
    action: SaveLoadAction = None
    button: str = None
    message: str = None
    requires_verification: bool = False


class FileMetaData:

    def __init__(self):
        self.file_exists: Optional[bool] = None
        self.date: Optional[float] = None

    def __repr__(self):
        return f"<{self.__class__.__name__} - exists={self.file_exists}, date={self.date}>"

    def store_metadata(self, file_path: Optional[pathlib.Path] = None):
        if file_path and os.path.isfile(file_path):
            self.date = os.path.getmtime(file_path)
            self.file_exists = True
        else:
            self.date = 0.
            self.file_exists = False
        return self

    def reset_metadata(self):
        self.date = None
        self.file_exists = None
        return self

    def get_file_status(self) -> FileStatus:
        if self.file_exists is None:
            return FileStatus.UNCHECKED
        return FileStatus.EXISTS if self.file_exists else FileStatus.MISSING

    def __eq__(self, other: 'FileMetaData'):
        return self.file_exists == other.file_exists and self.date == other.date


class FileSyncer(ABC):
    FILECOMPARISON_TO_TEXT = {
        FileComparison.CHANGED: '{} file has changed',
        FileComparison.DELETED: '{} file has been deleted',
        FileComparison.CREATED: 'new {} file has appeared',
        FileComparison.FILE_FOUND: '{} file exists',
        FileComparison.FILE_NOT_FOUND: '{} file does not exist',
    }

    NEEDFILE_INITIATING_TO_MESSAGE = {
        # is file   is
        # need      initiating   message
        (False,     True):      'there is no data to save',   # noqa: E241
        (False,     False):     'the data has been cleared',  # noqa: E241
        (True,      True):      'there is unsaved data',      # noqa: E241
        (True,      False):     'data has changed',           # noqa: E241
    }

    # What can happen upon Save:
    SAVE_LETTERCORE_TO_ACTION_BUTTON_QUESTION = {
        # Code               Action   Button       Question
        'V': (SaveLoadAction.NOTHING, '',          ''),                   # noqa: E241. do nothing. do not even propose
        '-': (SaveLoadAction.NONE,    '',          ''),                   # noqa: E241. do nothing
        'S': (SaveLoadAction.SAVE,    'Save',      'Save {} file'),       # noqa: E241. update saved file with new data
        'D': (SaveLoadAction.DELETE,  'Delete',    'Delete {} file'),     # noqa: E241. delete the file
        'C': (SaveLoadAction.SAVE,    'Create',    'Create {} file'),     # noqa: E241. create the file
        'R': (SaveLoadAction.SAVE,    'Recreate',  'Recreate {} file'),   # noqa: E241. recreate a just-deleted file
        'O': (SaveLoadAction.SAVE,    'Overwrite', 'Overwrite {} file'),  # noqa: E241. overwrite a changed file
    }

    # What can happen upon Load:
    LOAD_LETTERCODE_TO_ACTION_BUTTON_QUESTION = {
        # Code               Action   Button       Question
        'V': (SaveLoadAction.NOTHING, '',          ''),               # noqa: E241. do nothing. do not even propose
        '-': (SaveLoadAction.NONE,    '',          ''),               # noqa: E241. do nothing
        'L': (SaveLoadAction.LOAD,    'Load',      'Load {}'),        # noqa: E241. update data based on new file
        'C': (SaveLoadAction.CLEAR,   'Clear',     'Clear {}'),       # noqa: E241. clear data becuase of no file
        'O': (SaveLoadAction.LOAD,    'Overwrite', 'Overwrite {}',),  # noqa: E241. load while overwriting unsaved data
    }

    FILECOMPARISON_TO_SAVE_LOAD_LETTERCODES = {
        # Table copied from MatQuibbler:
        # letter codes are resolved in the tables above ('x' stands for options that are not possible)
        # capital letter-code indicates that action verification is not needed
        #
        # is_synced:                   Synced               Unsynced
        # need_file:                   Yes        No        Yes       No
        # has_data:                          Yes       No        Yes       No
        #                              Save  Load Save Load Save Load Save Load
        FileComparison.SAME_FILE:      ('-', '-', '-', '-', 'S', 'o', 'D', 'l'),  # noqa: E241
        FileComparison.NO_FILE:        ('-', '-', 'V', 'V', 'C', '-', 'V', 'V'),  # noqa: E241
        FileComparison.CHANGED:        ('o', 'L', 'd', 'L', 'o', 'l', 'd', 'L'),  # noqa: E241
        FileComparison.DELETED:        ('r', 'c', 'V', 'V', 'r', 'c', 'V', 'V'),  # noqa: E241
        FileComparison.CREATED:        ('o', 'L', 'd', 'L', 'o', 'l', 'd', 'L'),  # noqa: E241
        FileComparison.FILE_FOUND:     ('x', 'x', '-', '-', 'o', 'L', 'o', 'L'),  # noqa: E241
        FileComparison.FILE_NOT_FOUND: ('x', 'x', '-', '-', 'C', '-', 'V', 'V'),  # noqa: E241
    }

    @classmethod
    def _get_save_action_verification(cls, file_change: FileComparison, is_synced: bool, need_file: bool) \
            -> ActionVerification:
        code_letter = cls.FILECOMPARISON_TO_SAVE_LOAD_LETTERCODES[file_change][
            0 + (1 - is_synced) * 4 + (1 - need_file) * 2]
        logger.info(f"file_change - {file_change} is_synced - {is_synced} need file - {need_file}")
        return ActionVerification(*cls.SAVE_LETTERCORE_TO_ACTION_BUTTON_QUESTION[code_letter.capitalize()],
                                  code_letter != code_letter.capitalize())

    @classmethod
    def _get_load_action_verification(cls, file_change: FileComparison, is_synced: bool, has_data: bool) \
            -> ActionVerification:
        code_letter = cls.FILECOMPARISON_TO_SAVE_LOAD_LETTERCODES[file_change][
            1 + (1 - is_synced) * 4 + (1 - has_data) * 2]
        return ActionVerification(*cls.LOAD_LETTERCODE_TO_ACTION_BUTTON_QUESTION[code_letter.capitalize()],
                                  code_letter != code_letter.capitalize())

    def __init__(self):
        self.file_metadata: FileMetaData = FileMetaData()
        self.is_synced: bool = False

    @abstractmethod
    def _get_file_path(self) -> Optional[pathlib.Path]:
        """
        return full path to the file
        None if undefined
        """
        pass

    @abstractmethod
    def _has_data(self) -> bool:
        pass

    @abstractmethod
    def _should_create_empty_file_for_no_data(self) -> bool:
        pass

    @abstractmethod
    def _save_data_to_file(self, file_path: pathlib.Path):
        pass

    @abstractmethod
    def _load_data_from_file(self, file_path: pathlib.Path):
        pass

    @abstractmethod
    def _clear_data(self):
        pass

    @abstractmethod
    def _file_type(self) -> str:
        pass

    @abstractmethod
    def _dialog_title(self) -> str:
        pass

    def on_file_name_changed(self):
        """
        must be called when the file name changes
        """
        self.is_synced = False
        self.file_metadata.reset_metadata()

    def on_data_changed(self):
        """
        must be called when the data to be saved has changed
        """
        self.is_synced = False

    @property
    def need_file(self):
        return self._has_data() or self._should_create_empty_file_for_no_data()

    def _update_file_metadata(self):
        self.file_metadata.store_metadata(self._get_file_path())

    def _get_file_comparison(self) -> FileComparison:
        old_metadata = self.file_metadata
        new_metadata = FileMetaData().store_metadata(self._get_file_path())
        return FILE_STATUSES_TO_FILECOMPARISON[
            (old_metadata.get_file_status(), new_metadata.get_file_status(), new_metadata == old_metadata)]

    def _get_what_happened_message(self, file_comparison):
        what_happened_messages = []

        file_comparison_text = self.FILECOMPARISON_TO_TEXT.get(file_comparison)
        if file_comparison_text:
            what_happened_messages.append(file_comparison_text.format(self._file_type()))

        if not self.is_synced:
            what_happened_messages.append(
                self.NEEDFILE_INITIATING_TO_MESSAGE[
                    (self.need_file, file_comparison in [FileComparison.FILE_FOUND, FileComparison.FILE_NOT_FOUND])])

        return ' and '.join(what_happened_messages).capitalize() + '.'

    def _verify_action(self, file_comparison: FileComparison, action_verification: ActionVerification) -> bool:
        if not action_verification.requires_verification:
            return True
        from pyquibbler import Project
        answer = Project.get_or_create().text_dialog(self._dialog_title(),
                                                     self._get_what_happened_message(file_comparison) + '\n'
                                                     + action_verification.message.format(self._file_type()) + '?',
                                                     {'1': action_verification.button, '2': 'Skip'})

        return answer == '1'

    def get_save_command(self, file_comparison: Optional[FileComparison]) -> ActionVerification:
        file_comparison = file_comparison or self._get_file_comparison()
        return self._get_save_action_verification(file_comparison, self.is_synced, self.need_file)

    def save(self, skip_user_verification: bool = False):
        file_comparison = self._get_file_comparison()
        save_command = self.get_save_command(file_comparison)
        if skip_user_verification or self._verify_action(file_comparison, save_command):
            self._do_action(save_command.action)

    def get_load_command(self, file_comparison: Optional[FileComparison]) -> ActionVerification:
        file_comparison = file_comparison or self._get_file_comparison()
        return self._get_load_action_verification(file_comparison, self.is_synced, self._has_data())

    def load(self, skip_user_verification: bool = False):
        file_comparison = self._get_file_comparison()
        load_command = self.get_load_command(file_comparison)
        if skip_user_verification or self._verify_action(file_comparison, load_command):
            self._do_action(load_command.action)

    def _do_action(self, action: SaveLoadAction):
        if action == SaveLoadAction.SAVE:
            os.makedirs(self._get_file_path().parents[0], exist_ok=True)
            self._save_data_to_file(self._get_file_path())
        elif action == SaveLoadAction.DELETE:
            os.remove(self._get_file_path())
        elif action == SaveLoadAction.LOAD:
            self._load_data_from_file(self._get_file_path())
        elif action == SaveLoadAction.CLEAR:
            self._clear_data()

        self._update_file_metadata()
        self.is_synced = True

    def sync(self):
        file_comparison = self._get_file_comparison()
        save_command = self._get_save_action_verification(file_comparison, self.is_synced, self.need_file)
        load_command = self._get_load_action_verification(file_comparison, self.is_synced, self._has_data())
        if not save_command.action.is_action() and not load_command.action.is_action():
            action = SaveLoadAction.NOTHING
        elif load_command.action.is_action() \
                and (not save_command.action.is_action()
                     or save_command.requires_verification and not load_command.requires_verification):
            action = load_command.action
        elif save_command.action.is_action() \
                and (not load_command.action.is_action()
                     or load_command.requires_verification and not save_command.requires_verification):
            action = save_command.action
        else:
            from pyquibbler import Project
            answer = Project.get_or_create().text_dialog(self._dialog_title(),
                                                         self._get_what_happened_message(file_comparison),
                                                         {'1': save_command.message.format(self._file_type()),
                                                          '2': load_command.message.format(self._file_type()),
                                                          '3': 'Skip'})
            action = {'1': save_command.action,
                      '2': load_command.action,
                      '3': SaveLoadAction.NOTHING}[answer]

        self._do_action(action)
