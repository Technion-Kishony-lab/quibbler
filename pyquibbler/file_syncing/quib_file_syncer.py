import pathlib
import weakref
from typing import Optional
from .file_syncer import FileSyncer
from pyquibbler.utils import Flag
from typing import TYPE_CHECKING

from .types import SaveFormat

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


KEEP_EMPTY_FILE = Flag(False)


class QuibFileSyncer(FileSyncer):
    def __init__(self, quib_weakref: weakref.ref["Quib"]):
        self.quib_weakref = quib_weakref
        super(QuibFileSyncer, self).__init__()

    def _get_file_path(self) -> Optional[pathlib.Path]:
        return self.quib.file_path

    def _has_data(self) -> bool:
        return len(self.quib.get_override_list()) > 0

    def _should_create_empty_file_for_no_data(self) -> bool:
        return bool(KEEP_EMPTY_FILE)

    def _save_data_to_file(self, file_path: pathlib.Path):
        self.handler.save_assignments(file_path)

    def _load_data_from_file(self, file_path: pathlib.Path):
        self.handler.load_assignments(file_path)

    def _clear_data(self):
        pass
#        self.quib.assign() = np.zeros((1, 0), dtype=np.uint)

    def _file_type(self) -> str:
        return 'assignment'

    def _dialog_title(self) -> str:
        return self.quib.name

    @property
    def quib(self):
        return self.quib_weakref()

    @property
    def handler(self):
        return self.quib.handler

    @property
    def overrider(self):
        return self.handler.overrider