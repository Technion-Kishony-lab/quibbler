from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, List, Optional, Set
import pathlib

import numpy as np

from .assignment import AssignmentTemplate
from .assignment.assignment import PathComponent
from .quib import Quib
from .utils import is_there_a_quib_in_object
from ..env import DEBUG, PRETTY_REPR
from ..exceptions import DebugException, PyQuibblerException


@dataclass
class CannotNestQuibInIQuibException(DebugException):
    iquib: InputQuib

    def __str__(self):
        return 'Cannot create an input quib that contains another quib'


@dataclass
class CannotSaveAsTextException(PyQuibblerException):
    pass


class InputQuib(Quib):
    _DEFAULT_ALLOW_OVERRIDING = True

    def __init__(self, value: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Creates an InputQuib instance containing the given value.
        """
        super().__init__(assignment_template=assignment_template)
        self._value = value
        if DEBUG:
            if is_there_a_quib_in_object(value, force_recursive=True):
                raise CannotNestQuibInIQuibException(self)

        from .graphics.quib_guard import is_within_quib_guard, get_current_quib_guard
        if is_within_quib_guard():
            quib_guard = get_current_quib_guard()
            quib_guard.add_allowed_quib(self)

    def _get_inner_value_valid_at_path(self, path: List[PathComponent]) -> Any:
        """
        No need to do any calculation, this is an input quib.
        """
        return self._value

    def _get_paths_for_children_invalidation(self, invalidator_quib: 'Quib',
                                             path: List['PathComponent']) -> List[Optional[List[PathComponent]]]:
        """
        If an input quib is invalidated at a certain path, we want to invalidate our children at that path- as we are
        not performing any change on it (as opposed to a transpositional quib)
        """
        return [path]

    def __repr__(self):
        if PRETTY_REPR:
            return self.pretty_repr()
        return f'<{self.__class__.__name__} ({self.get_value()})>'

    def _get_inner_functional_representation_expression(self):
        return f'iquib({repr(self._value)})'

    @property
    def parents(self) -> Set[Quib]:
        return set()

    @property
    def _default_save_directory(self) -> Optional[pathlib.Path]:
        return self.project.input_quib_directory

    @property
    def _save_txt_path(self) -> Optional[pathlib.Path]:
        return self._save_directory / f"{self.name}.txt" if self._default_save_directory else None

    def save_as_txt(self):
        """
        Save the iquib as a text file. In contrast to the normal save, this will save the value of the quib regardless
        of whether the quib has overrides, as a txt file is used for the user to be able to see the quib and change it
        in a textual manner.
        Note that this WILL fail with CannotSaveAsTextException in situations where the iquib
        cannot be represented textually.
        The normal iquib's save_if_relevant() will still work in these situations
        """
        value = self.get_value()
        os.makedirs(self._default_save_directory, exist_ok=True)
        try:
            if isinstance(value, np.ndarray):
                np.savetxt(str(self._save_txt_path), value)
            else:
                with open(self._save_txt_path, 'w') as f:
                    json.dump(value, f)
        except TypeError:
            if os.path.exists(self._save_txt_path):
                os.remove(self._save_txt_path)
            raise CannotSaveAsTextException()

    def load(self):
        """
        Load the quib- this will attempt to load from a text file if possible and if not attempt a load from a binary
        file
        """
        if os.path.exists(self._save_txt_path):
            self._load_from_txt()
        return super(InputQuib, self).load()

    def _load_from_txt(self):
        """
        Load the quib from the corresponding text file is possible
        """
        if self._save_txt_path and os.path.exists(self._save_txt_path):
            if issubclass(self.get_type(), np.ndarray):
                self.assign_value(np.array(np.loadtxt(str(self._save_txt_path)), dtype=self.get_value().dtype))
            else:
                with open(self._save_txt_path, 'r') as f:
                    self.assign_value(json.load(f))


iquib = InputQuib
