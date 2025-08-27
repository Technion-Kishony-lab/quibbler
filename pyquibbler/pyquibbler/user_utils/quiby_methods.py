"""
Class decoration utilities for quiby functionality.
"""
from typing import Dict, Callable, Type

from pyquibbler.user_utils.quiby_funcs import is_quiby
from pyquibbler.utilities.get_original_func import get_original_func


def _is_method_of_kind(cls: Type, method_name: str, kind) -> bool:
    if method_name not in cls.__dict__:
        return False
    method = cls.__dict__[method_name]
    method = get_original_func(method)
    return isinstance(method, kind)


def is_static_method(cls: Type, method_name: str) -> bool:
    return _is_method_of_kind(cls, method_name, staticmethod)


def is_class_method(cls: Type, method_name: str) -> bool:
    return _is_method_of_kind(cls, method_name, classmethod)


def is_regular_method(cls: Type, method_name: str) -> bool:
    return method_name in cls.__dict__ and callable(getattr(cls, method_name)) \
        and not _is_method_of_kind(cls, method_name, (staticmethod, classmethod))


def is_property(cls: Type, attribute_name: str) -> bool:
    attribute = cls.__dict__.get(attribute_name, None)
    if attribute is None:
        return False
    return isinstance(attribute, property) and attribute.fget is not None


def get_methods_to_quibify(cls: Type) -> Dict[str, Callable]:
    """Get all methods that should be made quiby by the class decorator."""
    methods: Dict[str, Callable] = {}

    for name in dir(cls):

        if name.startswith('__') and name.endswith('__'):
            continue  # Skip magic methods (dunder methods)
        if not (is_regular_method(cls, name) or is_class_method(cls, name)):
            continue

        method = getattr(cls, name)

        if getattr(get_original_func(method), '__not_quiby__', False):
            continue
        if is_quiby(method):
            continue  # skip already quiby methods (Method precedence over class decoration)

        methods[name] = method

    return methods


def get_properties_to_quibify(cls: Type) -> Dict[str, property]:
    """Get all properties that should be made quiby by the class decorator."""
    properties: Dict[str, property] = {}

    for name, attribute in cls.__dict__.items():
        if not is_property(cls, name):
            continue
        original_getter = attribute.fget
        if getattr(get_original_func(original_getter), '__not_quiby__', False):
            continue
        if is_quiby(original_getter):
            continue
        properties[name] = attribute

    return properties

