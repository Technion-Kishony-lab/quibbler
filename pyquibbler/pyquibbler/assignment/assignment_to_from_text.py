from __future__ import annotations

from dataclasses import dataclass, field

from typing import List, Optional, Iterable

import numpy as np

from .default_value import default
from .assignment import Assignment

from pyquibbler.path import Path, PathComponent
from pyquibbler.quib.exceptions import CannotLoadAssignmentsFromTextException

ASSIGNMENT_VALUE_TEXT_DICT = {'array': np.array, 'default': default}


@dataclass
class GetReference:
    assignments: List[Assignment] = field(default_factory=list)
    current_path: Path = field(default_factory=list)

    def _add_key_to_path(self, key):
        self.current_path.append(PathComponent(None, key))

    def __getitem__(self, key):
        self._add_key_to_path(key)
        return self

    def __setitem__(self, key, value):
        self._add_key_to_path(key)
        self.assign(value)

    def assign(self, value):
        self.assignments.append(Assignment(value, self.current_path))
        self.current_path = []


def convert_executable_text_to_assignments(assignment_text: str) -> List[Assignment]:
    try:
        quib = GetReference()
        exec(assignment_text, {'quib': quib, **ASSIGNMENT_VALUE_TEXT_DICT})
        return quib.assignments
    except Exception:
        raise CannotLoadAssignmentsFromTextException(assignment_text) from None


def convert_assignments_to_executable_text(assignments: Iterable[Assignment], name: Optional[str] = None) -> str:
    name = 'quib' if name is None else name
    pretty = ''
    for assignment in assignments:
        pretty_value = assignment.get_pretty_value()
        pretty += '\n' + name
        if assignment.path:
            pretty += assignment.get_pretty_path()
            pretty += ' = ' + pretty_value
        else:
            pretty += '.assign(' + pretty_value + ')'
    pretty = pretty[1:] if pretty else pretty  # remove '\n'
    return pretty


def convert_simplified_text_to_assignment(assignment_text: str) -> Assignment:
    assignment_text = assignment_text.strip()

    if assignment_text.startswith('='):
        # '= value'
        assignment_text = f'quib.assign({assignment_text[1:]})'
    else:
        try:
            eval(assignment_text, ASSIGNMENT_VALUE_TEXT_DICT)  # triggers exception if text is an assignment statement
            # 'value'
            assignment_text = f'quib.assign({assignment_text})'
        except Exception:
            # 'path = value'
            assignment_text = f'quib{assignment_text}'

    assignments = convert_executable_text_to_assignments(assignment_text)

    if len(assignments) != 1:
        raise CannotLoadAssignmentsFromTextException(assignment_text) from None

    return assignments[0]


def convert_assignment_to_simplified_text(assignment: Assignment) -> str:
    if len(assignment.path) == 0:
        return '= ' + assignment.get_pretty_value()

    return assignment.get_pretty_path() + ' = ' + assignment.get_pretty_value()
