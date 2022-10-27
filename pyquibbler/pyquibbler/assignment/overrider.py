import pathlib
import pickle

import numpy as np

from typing import Any, Optional, Dict, Hashable, List

from pyquibbler.path.hashable import get_hashable_path
from pyquibbler.path.path_component import Path, Paths
from pyquibbler.path.data_accessing import deep_get, deep_set
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.utilities.iterators import recursively_run_func_on_object

from pyquibbler.debug_utils import timeit, logger

from .assignment import Assignment
from .assignment_to_from_text import convert_executable_text_to_assignments, convert_assignments_to_executable_text
from .assignment_template import AssignmentTemplate
from .default_value import default
from .exceptions import NoAssignmentFoundAtPathException, CannotConvertAssignmentsToTextException

PathsToAssignments = Dict[Hashable, Assignment]


class Overrider:
    """
    Gathers assignments performed on a quib and apply these assignments on the quib's value.
    """

    def __init__(self):
        self._paths_to_assignments: PathsToAssignments = {}
        self._active_assignment = None

    def clear_assignments(self) -> Paths:
        return self.replace_assignments({})

    def replace_assignments(self, new_paths_to_assignments: PathsToAssignments) -> Paths:
        """
        replace assignment list and return the changed paths
        """
        self._paths_to_assignments = new_paths_to_assignments
        self._active_assignment = None
        # TODO: invalidate only the changed paths
        return [[]]

    def _add_to_paths_to_assignments(self, assignment: Assignment):
        hashable_path = get_hashable_path(assignment.path)
        # We need to first remove and then add to make sure the new key value pair are now first in the dict
        if hashable_path in self._paths_to_assignments:
            self._paths_to_assignments.pop(hashable_path)
        self._paths_to_assignments[hashable_path] = assignment

    def add_assignment(self, assignment: Assignment):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._active_assignment = assignment
        self._add_to_paths_to_assignments(assignment)

    def pop_assignment_at_path(self, path: Path, raise_on_not_found: bool = True):
        hashable_path = get_hashable_path(path)
        if raise_on_not_found and hashable_path not in self._paths_to_assignments:
            raise NoAssignmentFoundAtPathException(path=path)
        return self._paths_to_assignments.pop(hashable_path, None)

    def pop_assignment_at_index(self, index: int):
        new_paths_with_assignments = list(self._paths_to_assignments.items())
        _, assignment = new_paths_with_assignments.pop(index)
        self._paths_to_assignments = dict(new_paths_with_assignments)
        return assignment

    def insert_assignment_at_index(self, assignment: Assignment, index: int):
        hashable_path = get_hashable_path(assignment.path)
        new_paths_with_assignments = list(self._paths_to_assignments.items())
        index = min(index, len(new_paths_with_assignments))  # see test_drag_xy_undo
        new_paths_with_assignments.insert(index, (hashable_path, assignment))

        # We need to remove any assignments with the same path that came before this index so we don't accidentally
        # use those (previous) assignments when running `dict` on the list
        for i, (path, assignment) in enumerate(new_paths_with_assignments[:index][:]):
            if hashable_path == path:
                new_paths_with_assignments.pop(i)

        logger.info(f"New paths with assignments {new_paths_with_assignments}")
        self._paths_to_assignments = dict(new_paths_with_assignments)

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Deep copies the argument and returns said data with applied overrides
        """
        original_data = data
        with timeit("quib_overriding"):
            data = deep_copy_without_quibs_or_graphics(data)
            for assignment in self._paths_to_assignments.values():
                if assignment.is_default():
                    value = deep_get(original_data, assignment.path)
                else:
                    value = assignment.value
                with external_call_failed_exception_handling():
                    data = deep_set(data, assignment.path, value,
                                    raise_on_failure=assignment is self._active_assignment)

        self._active_assignment = None
        return data

    def fill_override_mask(self, false_mask):
        """
        Given a mask in the desired shape with all values set to False, update it so
        all cells in overridden indexes will be set to True.
        """
        mask = false_mask
        for assignment in self:
            path = assignment.path
            val = assignment.value is not default
            if path:
                if isinstance(path[-1].component, slice):
                    inner_data = deep_get(mask, path[:-1])
                    if not isinstance(inner_data, np.ndarray):
                        val = recursively_run_func_on_object(lambda x: val, inner_data)
                mask = deep_set(mask, path, val)
            else:
                if val:
                    mask = np.ones(np.shape(assignment.value), dtype=bool)
                else:
                    mask = false_mask

        return mask

    def get(self, path: Path, default_value: bool = None) -> Assignment:
        """
        Get the assignment at the given path
        """
        return self._paths_to_assignments.get(get_hashable_path(path), default_value)

    def __getitem__(self, item) -> Assignment:
        return list(self._paths_to_assignments.values())[item]

    def __len__(self):
        return len(self._paths_to_assignments)

    """
    save/load
    """

    def save_as_binary(self, file: pathlib.Path):
        with open(file, 'wb') as f:
            pickle.dump(self._paths_to_assignments, f)

    def load_from_binary(self, file: pathlib.Path) -> List[Path]:
        with open(file, 'rb') as f:
            return self.replace_assignments(pickle.load(f))

    def save_as_txt(self, file: pathlib.Path):
        text = convert_assignments_to_executable_text(self._paths_to_assignments.values(),
                                                      raise_if_not_reversible=True)
        with open(file, "wt") as f:
            f.write(text)

    def load_from_assignments_text(self, assignment_text: str):
        self.clear_assignments()
        for assignment in convert_executable_text_to_assignments(assignment_text):
            self.add_assignment(assignment)
        return [[]]

    def load_from_txt(self, file: pathlib.Path):
        """
        load assignments from text file.
        """
        with open(file, mode='r') as f:
            assignment_text_commands = f.read()
        return self.load_from_assignments_text(assignment_text_commands)

    """
    repr
    """

    def get_pretty_repr(self, name: str = None):
        try:
            text = convert_assignments_to_executable_text(self._paths_to_assignments.values(), name)
        except CannotConvertAssignmentsToTextException:
            text = '[Cannot convert assignments to text]'
        return text

    def __repr__(self):
        return self.get_pretty_repr()
