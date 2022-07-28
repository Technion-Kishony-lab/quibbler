import enum
import pathlib
from dataclasses import dataclass
from .. import Quib
from ...env import REPR_RETURNS_SHORT_NAME


PROPERTY_LIST = (
    ('Function', ('func', 'is_iquib', 'is_random', 'is_file_loading', 'is_graphics', 'pass_quibs')),
    ('Arguments', ('args', 'kwargs')),
    ('File saving', (('save_format', 'actual_save_format'), 'file_path')),
    ('Assignments', ('assignment_template', 'allow_overriding', 'assigned_quibs')),
    ('Caching', ('cache_mode', 'cache_status')),
    ('Graphics', (('graphics_update', 'actual_graphics_update'), 'is_graphics_quib')),
)


def _repr(value):
    """
    repr for Enum, str, Path
    """
    if isinstance(value, enum.Enum):
        return value.name
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


@dataclass
class QuibViewer:
    """
    Display quib properties

    Provides a text (repr) and html (_repr_html_) display of the key properties of a quib

    Parameters
    ----------
    quib : Quib
        The quib whose properties to display.

    See Also
    --------
    Quib.display
    """
    quib: Quib

    def get_headers_to_props_to_values(self):
        headers_to_props_to_values = dict()
        with REPR_RETURNS_SHORT_NAME.temporary_set(True):
            for header, properties in PROPERTY_LIST:
                props_to_values = dict()
                for prop in properties:
                    is_actual_property = isinstance(prop, tuple)
                    if is_actual_property:
                        prop, actual_prop = prop
                        actual_value = getattr(self.quib, actual_prop)
                    value = getattr(self.quib, prop)
                    if is_actual_property:
                        values = (value, actual_value)
                    else:
                        values = (value, )
                    props_to_values[prop] = values
                headers_to_props_to_values[header] = props_to_values
        return headers_to_props_to_values

    def __repr__(self):
        repr_ = ''
        repr_ += f'{"quib":>20}: {self.quib}\n\n'
        headers_to_prop_to_values = self.get_headers_to_props_to_values()
        for header, props_to_values in headers_to_prop_to_values.items():
            repr_ += f'{"--- " + header + " ---":>20}\n'
            for prop, values in props_to_values.items():
                if len(values) == 1:
                    value, = values
                    repr_ += f'{prop:>20}: {_repr(value)}'
                else:
                    value, actual_value = values
                    repr_ += f'{prop:>20}: {_repr(value)}'
                    if value is None:
                        repr_ += f' -> {_repr(actual_value)}'
                repr_ += '\n'
            repr_ += '\n'
        return repr_
