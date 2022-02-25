from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import os
from enum import Enum
import pathlib
from typing import Union, Optional, Iterable, Tuple

import numpy as np


#  TODO: should be replaced with more fancy dialog box
def text_dialog(title: str, message: str, buttons_and_options: Iterable[Tuple[str, str]]) -> str:
    print(title)
    print(message)
    for button, option in buttons_and_options:
        print(button, ': ', option)
    while True:
        choice = input()
        if choice in [button for button, _ in buttons_and_options]:
            break
    return choice


class FileStatus(Enum):
    UNCHECKED = 0
    MISSING = 1
    EXISTS = 2


class FileComparison(Enum):
    SAMEFILE = 0,  # the file existed and did not change
    CHANGED = 1,  # the file existed and changed
    DELETED = 2,  # a file was deleted
    CREATED = 3,  # a file was created
    NOFILE = 4,  # file did not exist and still does not exist
    FILEFOUND = 5,  # the file was found upon initiation
    FILENOTFOUND = 6,  # the file was not found upon initiation


FILE_STATUSES_TO_FILECOMPARISON = {
    (FileStatus.EXISTS, FileStatus.EXISTS, True): FileComparison.SAMEFILE,
    (FileStatus.EXISTS, FileStatus.EXISTS, False): FileComparison.CHANGED,
    (FileStatus.EXISTS, FileStatus.MISSING, False): FileComparison.DELETED,
    (FileStatus.MISSING, FileStatus.EXISTS, False): FileComparison.CREATED,
    (FileStatus.MISSING, FileStatus.MISSING, True): FileComparison.NOFILE,
    (FileStatus.UNCHECKED, FileStatus.MISSING, False): FileComparison.FILENOTFOUND,
    (FileStatus.UNCHECKED, FileStatus.EXISTS, False): FileComparison.FILEFOUND,
}


class SaveAction(Enum):
    NOTHING = 0  # do nothing. do not even propose
    NONE = 1  # do nothing
    SAVE = 2  # save to file
    DELETE = 3  # delete the file

    def is_action(self):
        return self._value_ >= 2


class LoadAction(Enum):
    NOTHING = 0  # do nothing. do not even propose
    NONE = 1  # do nothing
    LOAD = 2  # laod date from file
    CLEAR = 3  # clear the data

    def is_action(self):
        return self._value_ >= 2


@dataclass
class ActionVerification:
    action: Union[SaveAction, LoadAction] = None
    button: str = None
    message: str = None
    requires_verification: bool = False


class FileMetaData:

    def __init__(self, file_path: Optional[pathlib.Path] = None):
        self.file_exists: Optional[bool] = None
        self.date: Optional[float] = None
        if file_path:
            self.store_metadata(file_path)

    def store_metadata(self, file_path):
        if file_path and os.path.isfile(file_path):
            self.date = os.path.getmtime(file_path)
            self.file_exists = True
        else:
            self.date = 0.
            self.file_exists = False

    def reset_metadata(self):
        self.date = None
        self.file_exists = None

    def get_file_status(self) -> FileStatus:
        if self.file_exists is None:
            return FileStatus.UNCHECKED
        return FileStatus.EXISTS if self.file_exists else FileStatus.MISSING

    def __eq__(self, other: 'FileMetaData'):
        return self.file_exists == other.file_exists and self.date == other.date


class SyncDataWithFile(ABC):
    FILECOMPARISON_TO_TEXT = {
        FileComparison.CHANGED: '{} file has changed',
        FileComparison.DELETED: '{} file has been deleted',
        FileComparison.CREATED: 'new {} file has appeared',
        FileComparison.FILEFOUND: '{} file exists',
        FileComparison.FILENOTFOUND: '{} file does not exist',
    }

    NEEDFILE_INITIATING_TO_MESSAGE = {
        (False, True): 'there is no data to save',
        (False, False): 'the data has been cleared',
        (True, True): 'there is unsaved data',
        (True, False): 'data has changed',
    }

    # What can happen upon Save:
    SAVE_LETTERCORE_TO_ACTION_BUTTON_QUESTION = {
        # Code           Action   Button       Question
        'V': (SaveAction.NOTHING, '', ''),  # do nothing. do not even propose
        '-': (SaveAction.NONE, '', ''),  # do nothing
        'S': (SaveAction.SAVE, 'save', 'Save {} file'),  # update a saved file with new data
        'D': (SaveAction.DELETE, 'delete', 'Delete {} file'),  # delete the file
        'C': (SaveAction.SAVE, 'create', 'Create {} file'),  # create the file
        'R': (SaveAction.SAVE, 'recreate', 'Recreate {} file'),  # recreate a just-deleted file
        'O': (SaveAction.SAVE, 'overwrite', 'Overwrite {} file'),  # overwrite a changed file
    }

    # What can happen upon Load:
    LOAD_LETTERCODE_TO_ACTION_BUTTON_QUESTION = {
        # Code           Action   Button       Question
        'V': (LoadAction.NOTHING, '', ''),  # do nothing. do not even propose
        '-': (LoadAction.NONE, '', ''),  # do nothing
        'L': (LoadAction.LOAD, 'load', 'Load {}'),  # update data based on new file
        'C': (LoadAction.CLEAR, 'clear', 'clear {}'),  # clear data becuase of no file
        'O': (LoadAction.LOAD, 'overwrite', 'Overwrite {}',),  # load data from file overwriting unsaved data
    }

    FILECOMPARISON_TO_SAVE_LOAD_LETTERCODES = {
        # Table copied from MatQuibbler:
        # is_synced:                  Synced    Synced    Unsynced  Unsynced
        # need_file:                  Yes       No        Yes       No
        # has_data:                   Yes       No        Yes       No
        #                             Sv   Ld   Sv   Ld   Sv   Ld   Sv   Ld
        FileComparison.SAMEFILE:     ('-', '-', '-', '-', 'S', 'o', 'D', 'l'),
        FileComparison.NOFILE:       ('-'  '-', 'v', 'v', 'C'  'c', 'v', 'v'),
        FileComparison.CHANGED:      ('o', 'L', 'd', 'L', 'o', 'l', 'd', 'L'),
        FileComparison.DELETED:      ('r', 'c', 'v', 'v', 'r', 'c', 'v', 'v'),
        FileComparison.CREATED:      ('o', 'L', 'd', 'L', 'o', 'l', 'd', 'L'),
        FileComparison.FILEFOUND:    (' ', ' ', ' ', ' ', 'o', 'L', 'o', 'L'),  # not possible for isSaved=true
        FileComparison.FILENOTFOUND: (' ', ' ', ' ', ' ', 'C', 'c', 'v', 'v'),  # not possible for isSaved=true
    }

    @classmethod
    def _get_save_action_verification(cls, file_change: FileComparison, is_synced: bool, need_file: bool) \
            -> ActionVerification:
        code_letter = cls.FILECOMPARISON_TO_SAVE_LOAD_LETTERCODES[file_change][
            0 + (1 - is_synced) * 4 + (1 - need_file) * 2]
        return ActionVerification(*cls.SAVE_LETTERCORE_TO_ACTION_BUTTON_QUESTION[code_letter.capitalize()],
                                  code_letter != code_letter.capitalize())

    @classmethod
    def _get_load_action_verification(cls, file_change: FileComparison, is_synced: bool, need_file: bool) \
            -> ActionVerification:
        code_letter = cls.FILECOMPARISON_TO_SAVE_LOAD_LETTERCODES[file_change][
            1 + (1 - is_synced) * 4 + (1 - need_file) * 2]
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

    def file_name_changed(self):
        """
        must be called when the file name changes
        """
        self.is_synced = False
        self.file_metadata.reset_metadata()

    def data_changed(self):
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
        new_metadata = FileMetaData(self._get_file_path())
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
                    (self.need_file, file_comparison in [FileComparison.FILEFOUND, FileComparison.FILENOTFOUND])])

        return ' and '.join(what_happened_messages)

    def _verify_action(self, file_comparison: FileComparison, action_verification: ActionVerification) -> bool:
        if not action_verification.requires_verification:
            return True
        answer = text_dialog(self._dialog_title(),
                             self._get_what_happened_message(file_comparison) + '\n'
                             + action_verification.message.format(self._file_type()) + '?',
                             (('1', action_verification.button), ('2', 'Skip')))
        return answer == '1'

    def save(self):
        file_comparison = self._get_file_comparison()
        save_command = self._get_save_action_verification(file_comparison, self.is_synced, self.need_file)
        if self._verify_action(file_comparison, save_command):
            self._do_save_action(save_command.action)

    def load(self):
        file_comparison = self._get_file_comparison()
        load_command = self._get_load_action_verification(file_comparison, self.is_synced, self.need_file)
        if self._verify_action(file_comparison, load_command):
            self._do_load_action(load_command.action)

    def _do_save_action(self, action: SaveAction):
        if action == SaveAction.SAVE:
            os.makedirs(self._get_file_path().parents[0], exist_ok=True)
            self._save_data_to_file(self._get_file_path())
        elif action == SaveAction.DELETE:
            os.remove(self._get_file_path())
        else:
            return

        self._update_file_metadata()
        self.is_synced = True

    def _do_load_action(self, action: LoadAction):
        if action == LoadAction.LOAD:
            self._load_data_from_file(self._get_file_path())
        elif action == LoadAction.CLEAR:
            self._clear_data()
        else:
            return

        self._update_file_metadata()
        self.is_synced = True

    def sync(self):
        file_comparison = self._get_file_comparison()
        save_command = self._get_save_action_verification(file_comparison, self.is_synced, self.need_file)
        load_command = self._get_load_action_verification(file_comparison, self.is_synced, self.need_file)
        if not save_command.action.is_action() and not load_command.action.is_action():
            return
        elif load_command.action.is_action() \
                and (not save_command.action.is_action()
                     or save_command.requires_verification and not load_command.requires_verification):
            self._do_load_action(load_command.action)
        elif save_command.action.is_action() \
                and (not load_command.action.is_action()
                     or load_command.requires_verification and not save_command.requires_verification):
            self._do_save_action(save_command.action)
        else:
            answer = text_dialog(self._dialog_title(),
                                 self._get_what_happened_message(file_comparison),
                                 (('1', save_command.message.format(self._file_type())),
                                  ('2', load_command.message.format(self._file_type())),
                                  ('3', 'Skip')))
            if answer == '1':
                self._do_save_action(save_command.action)
            if answer == '2':
                self._do_load_action(load_command.action)


@dataclass
class TestSyncDataWithFile(SyncDataWithFile):
    _file_name: str = field(default_factory=str)
    _data: Optional[np.ndarray] = None
    should_create_empty_file_for_no_data: bool = True

    def __post_init__(self):
        super(TestSyncDataWithFile, self).__init__()

    def _get_file_path(self) -> Optional[pathlib.Path]:
        return pathlib.Path(self.file_name).resolve()

    def _has_data(self) -> bool:
        return self.data is not None

    def _should_create_empty_file_for_no_data(self) -> bool:
        return self.should_create_empty_file_for_no_data

    def _save_data_to_file(self, file_path: pathlib.Path):
        np.savetxt(str(file_path), self.data)

    def _load_data_from_file(self, file_path: pathlib.Path):
        self.data = np.array(np.loadtxt(str(file_path)), dtype=np.uint8)

    def _clear_data(self):
        self.data = None

    def _file_type(self) -> str:
        return 'data'

    def _dialog_title(self) -> str:
        return 'my data'

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self.data_changed()

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, file_name):
        self._file_name = file_name
        self.file_name_changed()

    def __repr__(self):
        return \
            'TestSyncDataWithFile\n' \
            f'   data = {self.data}\n' \
            f'   file_name = {self.file_name}\n' \
            f'   empty_file = {self.should_create_empty_file_for_no_data}\n'


if __name__ == 'main':
    f = TestSyncDataWithFile()
    f.file_name = 'kuksi.txt'
    f.data = [1,2,3]
    f.save()
    f.load()
    f.data = [4,5,6]
    f.load()