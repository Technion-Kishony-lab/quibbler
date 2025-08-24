
from unittest import mock

import pytest

from pyquibbler import iquib, quiby, obj2quib, is_quiby
from pyquibbler.quib.graphics.event_handling.utils import is_quib
from pyquibbler.quib.quib import Quib


@quiby(pass_quibs=False)
def get_x_attr(obj):
    return obj.x


def test_get_attr_of_quib():
    class Obj:
        def __init__(self, x):
            self.x = x

    quib = iquib(5)
    obj = Obj(quib)
    x_attr = get_x_attr(obj)
    assert is_quib(x_attr)
    assert x_attr.get_value() == 5

    quib.assign(10)
    assert x_attr.get_value() == 10
