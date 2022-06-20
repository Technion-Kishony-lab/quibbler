import copy
import pathlib
import pickle
import re

import numpy as np
from typing import Any, Optional, Dict, Hashable, List

from .assignment import Assignment
from .exceptions import NoAssignmentFoundAtPathException
from ..path.hashable import get_hashable_path
from pyquibbler.path.path_component import Path, Paths, PathComponent
from .assignment_template import AssignmentTemplate
from ..path.data_accessing import deep_get, deep_assign_data_in_path
from .default_value import default

from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling


class getslice:
    def __getitem__(self, idx):
        return idx


def parse_getitem_reference(text: str):
    return eval(f"getslice()[{text}]", {'array': np.array, 'getslice': getslice})


def first_level_parenthesis(string):
    """Find all first-level [] parenthesized contents in string."""
    stack = []
    for i, c in enumerate(string):
        if c == '[':
            stack.append(i)
        elif c == ']' and stack:
            start = stack.pop()
            if len(stack) == 0:
                yield string[start + 1: i]


PathsToAssignments = Dict[Hashable, Assignment]


class Overrider:
    """
    Gathers function_definitions assignments performed on a quib in order to apply them on a quib value.
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
        assignment_without_indexed_cls = copy.deepcopy(assignment)
        for component in assignment_without_indexed_cls.path:
            component.indexed_cls = None

        self._active_assignment = assignment_without_indexed_cls
        self._add_to_paths_to_assignments(assignment_without_indexed_cls)

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
        new_paths_with_assignments = list(self._paths_to_assignments.items())
        new_paths_with_assignments.insert(index, (get_hashable_path(assignment.path), assignment))
        self._paths_to_assignments = dict(new_paths_with_assignments)

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Deep copies the argument and returns said data with applied overrides
        """
        from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics
        from pyquibbler import timer
        original_data = data
        with timer("quib_overriding"):
            data = deep_copy_without_quibs_or_graphics(data)
            for assignment in self._paths_to_assignments.values():
                if assignment.is_default():
                    value = deep_get(original_data, assignment.path)
                else:
                    value = assignment.value
                with external_call_failed_exception_handling():
                    data = deep_assign_data_in_path(data, assignment.path, value,
                                                    raise_on_failure=assignment == self._active_assignment)

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
                        from pyquibbler.utilities.iterators import recursively_run_func_on_object
                        val = recursively_run_func_on_object(lambda x: val, inner_data)
                mask = deep_assign_data_in_path(mask, path, val)
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

    def can_save_to_txt(self) -> bool:
        from pyquibbler.quib.utils.miscellaneous import is_saveable_as_txt
        for assignment in self._paths_to_assignments.values():
            if not is_saveable_as_txt([cmp.component for cmp in assignment.path]) \
                    or isinstance(assignment, Assignment) and not is_saveable_as_txt(assignment.value):
                return False
        return True

    def save_as_txt(self, file: pathlib.Path):
        from pyquibbler.quib.exceptions import CannotSaveAssignmentsAsTextException
        if not self.can_save_to_txt():
            raise CannotSaveAssignmentsAsTextException()
        with open(file, "wt") as f:
            f.write(self.pretty_repr())

    def load_from_assignment_text(self, assignment_text: str):
        from ..quib.exceptions import CannotLoadAssignmentsFromTextException

        self.clear_assignments()
        try:
            lines = assignment_text.split('\n')
            for line in lines:
                assert line.startswith('quib')
                if ' = ' in line:
                    left, value_text = line.split(' = ', 1)
                    path = [PathComponent(None, parse_getitem_reference(text_component))
                            for text_component in first_level_parenthesis(left)]
                else:
                    value_text = re.match(r".*\((.*?)\)", line).groups()[0]
                    path = []

                value = eval(value_text, {'array': np.array, 'default': default})
                self.add_assignment(Assignment(value=value, path=path))

        except Exception:
            raise CannotLoadAssignmentsFromTextException(assignment_text) from None
        return [[]]

    def load_from_txt(self, file: pathlib.Path):
        """
        load assignments from text file.
        """
        with open(file, mode='r') as f:
            assignment_text_commands = f.read()
        return self.load_from_assignment_text(assignment_text_commands)

    """
    repr
    """

    def pretty_repr(self, name: str = None):
        name = 'quib' if name is None else name
        from ..quib.pretty_converters.pretty_convert import getitem_converter
        pretty = ''
        for assignment in self._paths_to_assignments.values():
            pretty_value = repr(assignment.value) if isinstance(assignment, Assignment) else 'default'
            pretty += '\n' + name
            if assignment.path:
                pretty += ''.join([str(getitem_converter(None, ('', cmp.component))) for cmp in assignment.path])
                pretty += ' = ' + pretty_value
            else:
                pretty += '.assign(' + pretty_value + ')'
        pretty = pretty[1:] if pretty else pretty
        return pretty

    def __repr__(self):
        return self.pretty_repr()
