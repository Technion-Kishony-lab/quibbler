import enum
import pathlib
from dataclasses import dataclass
from .. import Quib
from ...env import REPR_RETURNS_SHORT_NAME
from ...utilities.file_path import PathToNotebook

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
    repr for Enum, str, Path, function
    """
    if isinstance(value, enum.Enum):
        return value.name
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, PathToNotebook):
        return repr(value)
    if isinstance(value, pathlib.Path):
        return str(value)
    if callable(value):
        # replace '<function cos at 0x1194d8af0>' -> '<function cos>'
        value = str(value)
        if len(value) > 16 and value[-16:-12] == ' at ' and value[-1] == '>':
            value = value[:-16] + '>'
    return value


def replace_lt_gt(text: str):
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def html_element(item, tag: str, props: str = '') -> str:
    return f'<{tag} {props}>{item}</{tag}>'


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
            actual_value_str = ''
            for prop, values in props_to_values.items():
                if len(values) == 1:
                    value, = values
                else:
                    value, actual_value = values
                    if value is None:
                        actual_value_str = f' -> {_repr(actual_value)}'
                value_str = f'{prop:>20}: {_repr(value)}'
                repr_ += value_str + actual_value_str + '\n'
            repr_ += '\n'
        return repr_

    def _repr_html_(self):
        repr_ = ''
        repr_ += '<!DOCTYPE html>'
        repr_ += '<html><body>'

        repr_ += html_element(self.quib, 'h3')

        headers_to_prop_to_values = self.get_headers_to_props_to_values()
        for header, props_to_values in headers_to_prop_to_values.items():
            repr_ += html_element(header, 'h5')
            table = ''
            for prop, values in props_to_values.items():
                left = html_element(html_element(f'{prop}:', 'div', 'style="float:right; font-weight:bold"'), 'td',
                                    'style="width:30%"')
                actual_value_str = ''
                if len(values) == 1:
                    value, = values
                else:
                    value, actual_value = values
                    if value is None:
                        actual_value_str = replace_lt_gt(f' &rarr; {_repr(actual_value)}')
                value_str = replace_lt_gt(f'{_repr(value)}')
                right = html_element(html_element(value_str + actual_value_str, 'div', 'style="float:left"'), 'td')

                row = html_element(left + right, 'tr', 'height:70%')
                table += row
            repr_ += html_element(table, 'table', 'style = "width:400px"')

        repr_ += '</body></html>'
        return repr_
