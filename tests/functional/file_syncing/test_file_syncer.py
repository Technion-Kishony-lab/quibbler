import os
import numpy as np
import pathlib
from dataclasses import dataclass, field
from pyquibbler.file_syncing.file_syncer import FileSyncer
from pytest import fixture

from typing import Optional


@dataclass
class ArrayFileSyncer(FileSyncer):
    _file_name: str = field(default_factory=str)
    _data: np.ndarray = field(default_factory=lambda: np.zeros((1, 0), dtype=np.uint))
    should_create_empty_file_for_no_data: bool = True

    def __post_init__(self):
        super(ArrayFileSyncer, self).__init__()

    def _get_file_path(self) -> Optional[pathlib.Path]:
        return pathlib.Path(self.file_name).resolve()

    def _has_data(self) -> bool:
        return self.data.size > 0

    def _should_create_empty_file_for_no_data(self) -> bool:
        return self.should_create_empty_file_for_no_data

    def _save_data_to_file(self, file_path: pathlib.Path):
        np.savetxt(str(file_path), self.data)

    def _load_data_from_file(self, file_path: pathlib.Path):
        self.data = np.loadtxt(str(file_path))

    def _clear_data(self):
        self.data = np.zeros((1, 0), dtype=np.uint)

    def _file_type(self) -> str:
        return 'data'

    def _dialog_title(self) -> str:
        return 'my data'

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = np.array(data, dtype=np.uint)
        self.on_data_changed()

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, file_name):
        self._file_name = file_name
        self.on_file_name_changed()

    def __repr__(self):
        return \
            'ArrayFileSyncer\n' \
            f'   data = {self.data}\n' \
            f'   file_name = {self.file_name}\n' \
            f'   empty_file = {self.should_create_empty_file_for_no_data}\n'


@fixture()
def file_path(tmpdir):
    return str(pathlib.Path(tmpdir.strpath) / 'data_file.txt')


@fixture()
def syncable_data(file_path):
    return ArrayFileSyncer(file_path)


def overwrite_file(path, data):
    data = np.array(data, dtype=np.uint)
    np.savetxt(str(path), data)


def read_file(path):
    data = np.loadtxt(path)
    return np.array(data, dtype=np.uint)


def test_save_load(file_path):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    new_syncable_array = ArrayFileSyncer(file_path)
    new_syncable_array.load()
    assert np.array_equal(syncable_array.data, new_syncable_array.data)


def test_save_then_change_data_then_load_reject(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    syncable_array.data = [4, 5, 6]
    monkeypatch.setattr('builtins.input', lambda: "2")
    syncable_array.load()
    assert capsys.readouterr().out == \
           'my data\n' \
           'Data has changed.\n' \
           'Overwrite data?\n' \
           '1 :  Overwrite\n' \
           '2 :  Skip\n'
    assert np.array_equal(syncable_array.data, [4, 5, 6])


def test_save_then_change_data_then_load_accept(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    syncable_array.data = [4, 5, 6]
    monkeypatch.setattr('builtins.input', lambda: "1")
    syncable_array.load()
    assert np.array_equal(syncable_array.data, [1, 2, 3])


def test_save_then_change_data_then_sync(file_path, monkeypatch):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    syncable_array.data = [4, 5, 6]
    syncable_array.sync()
    assert np.array_equal(read_file(file_path), [4, 5, 6])


def test_save_then_change_file_then_load(file_path, monkeypatch):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    overwrite_file(file_path, [4, 5, 6])
    syncable_array.load()
    assert np.array_equal(syncable_array.data, [4, 5, 6])


def test_save_then_change_file_then_sync(file_path, monkeypatch):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    overwrite_file(file_path, [4, 5, 6])
    syncable_array.sync()
    assert np.array_equal(syncable_array.data, [4, 5, 6])


def test_save_then_change_file_then_save_reject(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    overwrite_file(file_path, [4, 5, 6])
    monkeypatch.setattr('builtins.input', lambda: "2")
    syncable_array.save()
    assert capsys.readouterr().out == \
           'my data\n' \
           'Data file has changed.\n' \
           'Overwrite data file?\n' \
           '1 :  Overwrite\n' \
           '2 :  Skip\n'
    assert np.array_equal(read_file(file_path), [4, 5, 6])


def test_save_then_change_file_then_save_accept(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    overwrite_file(file_path, [4, 5, 6])
    monkeypatch.setattr('builtins.input', lambda: "1")
    syncable_array.save()
    assert np.array_equal(read_file(file_path), [1, 2, 3])


def test_initiate_with_file_and_sync(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    overwrite_file(file_path, [4, 5, 6])
    syncable_array.sync()
    assert np.array_equal(syncable_array.data, [4, 5, 6])


def test_initiate_without_file_and_sync(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.sync()
    assert np.array_equal(syncable_array.data, [1, 2, 3])
    assert np.array_equal(read_file(file_path), [1, 2, 3])


def test_save_then_change_file_and_data_then_sync_overwrite_file(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    overwrite_file(file_path, [4, 5, 6])
    syncable_array.data = [7, 8, 9]
    monkeypatch.setattr('builtins.input', lambda: "1")
    syncable_array.sync()
    assert capsys.readouterr().out == \
           'my data\n' \
           'Data file has changed and data has changed.\n' \
           '1 :  Overwrite data file\n' \
           '2 :  Load data\n' \
           '3 :  Skip\n'

    assert np.array_equal(read_file(file_path), [7, 8, 9])
    assert np.array_equal(syncable_array.data, [7, 8, 9])


def test_save_then_change_file_and_data_then_sync_load_file(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    overwrite_file(file_path, [4, 5, 6])
    syncable_array.data = [7, 8, 9]
    monkeypatch.setattr('builtins.input', lambda: "2")
    syncable_array.sync()

    assert np.array_equal(read_file(file_path), [4, 5, 6])
    assert np.array_equal(syncable_array.data, [4, 5, 6])


def test_save_then_delete_file_then_sync(file_path, monkeypatch, capsys):
    syncable_array = ArrayFileSyncer(file_path)
    syncable_array.data = [1, 2, 3]
    syncable_array.save()
    os.remove(file_path)
    monkeypatch.setattr('builtins.input', lambda: "2")
    syncable_array.sync()
    assert capsys.readouterr().out == \
           'my data\n' \
           'Data file has been deleted.\n' \
           '1 :  Recreate data file\n' \
           '2 :  Clear data\n' \
           '3 :  Skip\n'

    assert np.array_equal(syncable_array.data, np.zeros((1, 0), dtype=np.uint))



