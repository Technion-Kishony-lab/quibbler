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


def get_methods_to_quibify(cls: Type) -> Dict[str, Callable]:
    """Get all methods that should be made quiby by the class decorator."""
    methods = {}

    for name in dir(cls):
        # Skip magic methods (dunder methods)
        if name.startswith('__') and name.endswith('__'):
            continue
            
        if is_regular_method(cls, name) or is_class_method(cls, name):
            method = getattr(cls, name)
            # direct decoration of methods take precedence over class decoration
            # so we skip already quiby methods
            if not is_quiby(method):
                methods[name] = method

    return methods
