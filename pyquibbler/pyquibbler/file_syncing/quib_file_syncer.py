from __future__ import annotations

import pathlib
import weakref
from typing import Optional

from pyquibbler.utilities.basic_types import Flag
from .file_syncer import FileSyncer

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


KEEP_EMPTY_FILE = Flag(False)


class QuibFileSyncer(FileSyncer):
    def __init__(self, quib_ref: weakref.ReferenceType["Quib"]):
        self.quib_ref = quib_ref
        super(QuibFileSyncer, self).__init__()

    def _get_file_path(self) -> Optional[pathlib.Path]:
        return self.quib.file_path

    def _has_data(self) -> bool:
        return self.quib.handler.is_overridden

    def _should_create_empty_file_for_no_data(self) -> bool:
        return bool(KEEP_EMPTY_FILE)

    def _save_data_to_file(self, file_path: pathlib.Path):
        self.handler.save_assignments_or_value(file_path)

    def _load_data_from_file(self, file_path: pathlib.Path):
        self.handler.load_from_assignment_file_or_value_file(file_path)

    def _clear_data(self):
        self.handler.clear_all_overrides()

    def _file_type(self) -> str:
        return 'assignment'

    def _dialog_title(self) -> str:
        return self.quib.name

    @property
    def quib(self) -> Quib:
        return self.quib_ref()

    @property
    def handler(self):
        return self.quib.handler

    @property
    def overrider(self):
        return self.handler.overrider
