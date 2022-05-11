import matplotlib.pyplot as plt

from unittest import mock
from unittest.mock import Mock

import pytest

from pyquibbler import iquib
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode, redraw_axeses
from weakref import ref


def test_quibs_deleted_when_variable_clears():
    a = iquib(1)
    b = a + 2
    ref_a = ref(a)
    ref_b = ref(b)
    del a, b

    assert ref_a() is None
    assert ref_b() is None
