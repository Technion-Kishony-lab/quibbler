import pytest

from pyquibbler import iquib, CacheMode
from pyquibbler.file_syncing import SaveFormat
from pyquibbler.quib.graphics import GraphicsUpdateType
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException, InvalidArgumentValueException, \
    UnknownEnumException


@pytest.mark.parametrize(['prop_name', 'set_value', 'get_value'], [
    ('pass_quibs', True, True),
    ('save_format', 'off', SaveFormat.OFF),
    ('save_format', SaveFormat.VALUE_TXT, SaveFormat.VALUE_TXT),
    ('cache_mode', 'off', CacheMode.OFF),
    ('graphics_update', 'never', GraphicsUpdateType.NEVER),
    ('allow_overriding', False, False),
    ('assigned_quibs', [], set()),
    ('assigned_quibs', (), set()),
    ('assigned_quibs', None, None),
    ('assignment_template', None, None),
    ('save_directory', 'my_folder', PathWithHyperLink('my_folder')),
    ('save_directory', None, None),
    ('assigned_name', 'my_quib79', 'my_quib79'),
    ('name', 'my_quib79', 'my_quib79'),
])
def test_correctly_set_valid_values(prop_name, set_value, get_value):
    a = iquib(2)
    setattr(a, prop_name, set_value)
    assert getattr(a, prop_name) == get_value


@pytest.mark.parametrize(['prop_name', 'set_value', 'exception'], [
    ('pass_quibs', 1, InvalidArgumentTypeException),
    ('save_format', 2, InvalidArgumentTypeException),
    ('cache_mode', 'kuk', UnknownEnumException),
    ('graphics_update', True, InvalidArgumentTypeException),
    ('allow_overriding', 0, InvalidArgumentTypeException),
    ('assigned_quibs', (2, 3), InvalidArgumentValueException),
    ('assignment_template', 'kuk', InvalidArgumentTypeException),
    ('save_directory', 7, InvalidArgumentTypeException),
    ('assigned_name', 73, InvalidArgumentTypeException),
    ('assigned_name', '73', InvalidArgumentValueException),
    ('name', 73, InvalidArgumentTypeException),
    ('name', '73', InvalidArgumentValueException),
])
def test_reject_set_invlid_properties(prop_name, set_value, exception):
    a = iquib(2)
    with pytest.raises(exception):
        setattr(a, prop_name, set_value)


def test_set_assigned_quibs():
    a = iquib(2)
    b = iquib(3)
    a.assigned_quibs = {b}
    assert a.assigned_quibs == {b}
