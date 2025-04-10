import pathlib
import pickle

import numpy as np

from typing import Any, Optional, List, Tuple

from pyquibbler.path.path_component import Path, Paths
from pyquibbler.path.data_accessing import deep_get, deep_set
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.utilities.iterators import recursively_run_func_on_object

from pyquibbler.debug_utils import timeit

from .assignment import Assignment
from .assignment_to_from_text import convert_executable_text_to_assignments, convert_assignments_to_executable_text
from .assignment_template import AssignmentTemplate
from .default_value import default
from .exceptions import CannotConvertAssignmentsToTextException

Assignments = List[Assignment]
TwoAssignments = Tuple[Optional[Assignment], Optional[Assignment]]


class Overrider:
    """
    Gathers assignments performed on a quib and apply these assignments on the quib's value.
    """

    def __init__(self):
        self._assignments: Assignments = []
        self._active_assignment = None

    def get_assignments(self):
        return self._assignments

    def get_paths(self) -> Paths:
        return [assignment.path for assignment in self._assignments]

    def get_index_of_path(self, path: Path) -> int:
        """
        Returns the first index with assignment matching the specified path.
        """
        return self.get_paths().index(path)

    def get_assignment_index(self, assignment: Optional[Assignment]):
        """
        Returns the index of an assignment.
        If assignment=None, returns the len of the assignment list
        """
        return len(self) if assignment is None else self._assignments.index(assignment)

    def clear_assignments(self) -> Paths:
        """
        Clear all assignments. Return affected paths.
        """
        return self.replace_assignments([])

    def replace_assignments(self, new_assignments: Assignments) -> Paths:
        """
        Replace the assignment list with a new list and return affected paths
        """
        self._active_assignment = None
        old_paths = self.get_paths()
        self._assignments = new_assignments
        new_paths = self.get_paths()
        return old_paths + new_paths

    def remove_assignments_at_path(self, path: Path) -> TwoAssignments:
        """
        Remove assignment to specified path.
        Returns the removed assignment and the assignment next to it (or None if removed assignment is last).
        """
        try:
            index = self.get_index_of_path(path)
            return self.pop_assignment_at_index(index)
        except ValueError:
            return None, None

    def add_new_assignment_before_assignment(self,
                                             new_assignment: Assignment,
                                             next_assignment: Optional[Assignment] = None,
                                             ):
        """
        Add a new_assignment before a specified next_assignment
        next_assignment: the assignment before which the new assignment is added. None to add at the end.
        """
        self.insert_assignment_at_index(self.get_assignment_index(next_assignment), new_assignment)

    def add_assignment(self, new_assignment: Assignment) -> TwoAssignments:
        """
        Adds an override to the overrider.
        Remove prior assignments at the same path
        """
        self._active_assignment = new_assignment
        old_assignment_and_next = self.remove_assignments_at_path(new_assignment.path)
        self.add_new_assignment_before_assignment(new_assignment)
        return old_assignment_and_next

    def pop_assignment_at_index(self, index) -> TwoAssignments:
        """
        Remove assignment at specified index.
        Returns the removed assignment and the assignment after it (or None if last).
        """
        removed_assignment = self._assignments.pop(index)
        next_assignment = self._assignments[index] if index < len(self) else None
        return removed_assignment, next_assignment

    def pop_assignment_before_assignment(self, next_assignment: Optional[Assignment]) -> Assignment:
        return self.pop_assignment_at_index(self.get_assignment_index(next_assignment) - 1)

    def insert_assignment_at_index(self, index: Optional[int], assignment: Assignment) -> Optional[Assignment]:
        """
        Insert a new assignment at specified index.
        Returns the next assignment, or None if new assignment is inserted last
        """
        self._assignments.insert(index, assignment)
        return self._assignments[index + 1] if index + 1 < len(self) else None

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Deep copies the argument and returns said data with applied overrides
        """
        original_data = data
        with timeit("quib_overriding"):
            data = deep_copy_without_quibs_or_graphics(data)
            for assignment in self._assignments:
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
        for assignment in self._assignments:
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

    def get(self, path: Path) -> Assignment:
        """
        Get the assignment at the given path
        """
        return self._assignments[self.get_index_of_path(path)]

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]

    def __len__(self):
        return len(self._assignments)

    """
    save/load
    """

    def save_as_binary(self, file: pathlib.Path):
        with open(file, 'wb') as f:
            pickle.dump(self._assignments, f)

    def load_from_binary(self, file: pathlib.Path) -> List[Path]:
        with open(file, 'rb') as f:
            return self.replace_assignments(pickle.load(f))

    def save_as_txt(self, file: pathlib.Path):
        text = convert_assignments_to_executable_text(self._assignments,
                                                      raise_if_not_reversible=True)
        with open(file, "wt") as f:
            f.write(text)

    def load_from_assignments_text(self, assignment_text: str):
        new_assignments = convert_executable_text_to_assignments(assignment_text)
        return self.replace_assignments(new_assignments)

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
            text = convert_assignments_to_executable_text(self._assignments, name)
        except CannotConvertAssignmentsToTextException:
            text = '[Cannot convert assignments to text]'
        return text

    def __repr__(self):
        return self.get_pretty_repr()
