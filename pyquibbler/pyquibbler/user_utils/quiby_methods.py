"""
Class decoration utilities for quiby functionality.
"""
from typing import Dict, Callable, Type, NamedTuple, Union, List
from enum import Enum

from pyquibbler.user_utils.quiby_funcs import is_quiby
from pyquibbler.utilities.get_original_func import get_original_func


class QuibifiableAttribute(NamedTuple):
    name: str
    attribute: Union[Callable, property]  # The original descriptor/function
    wrapper_func: Callable  # Function that takes (attribute, wrapped_func) and returns the new descriptor


def _is_method_of_kind(cls: Type, method_name: str, kind) -> bool:
    # Check in the class hierarchy (MRO) to find where the method is defined
    for base_cls in cls.__mro__:
        if method_name in base_cls.__dict__:
            method = base_cls.__dict__[method_name]
            method = get_original_func(method)
            return isinstance(method, kind)
    return False


def is_static_method(cls: Type, method_name: str) -> bool:
    return _is_method_of_kind(cls, method_name, staticmethod)


def is_class_method(cls: Type, method_name: str) -> bool:
    return _is_method_of_kind(cls, method_name, classmethod)


def is_regular_method(cls: Type, method_name: str) -> bool:
    # Check if the method exists in the class hierarchy and is callable
    if not hasattr(cls, method_name):
        return False
    if not callable(getattr(cls, method_name)):
        return False
    # Make sure it's not a static method or class method
    return not _is_method_of_kind(cls, method_name, (staticmethod, classmethod))


def _get_attribute_from_mro(cls: Type, attribute_name: str):
    """Get attribute from class hierarchy (MRO)."""
    for base_cls in cls.__mro__:
        if attribute_name in base_cls.__dict__:
            return base_cls.__dict__[attribute_name]
    return None


def is_property(cls: Type, attribute_name: str) -> bool:
    # Check in the class hierarchy (MRO) to find where the property is defined
    attribute = _get_attribute_from_mro(cls, attribute_name)
    return isinstance(attribute, property) and attribute.fget is not None


def _wrap_property(attribute, quiby_func, *args, **kwargs):
    """Extract getter from property, wrap it, and recreate property."""
    wrapped_getter = quiby_func(attribute.fget, *args, **kwargs)
    return property(wrapped_getter, attribute.fset, attribute.fdel, attribute.__doc__)


def _wrap_classmethod(attribute, quiby_func, *args, **kwargs):
    """Extract function from classmethod, wrap it, and recreate classmethod."""
    wrapped_func = quiby_func(attribute.__func__, *args, **kwargs)
    return classmethod(wrapped_func)


def _wrap_instancemethod(attribute, quiby_func, *args, **kwargs):
    """Wrap instance method directly."""
    return quiby_func(attribute, *args, **kwargs)


def get_all_quibifiable_attributes(cls: Type) -> List[QuibifiableAttribute]:
    """Get all attributes (methods and properties) that should be made quiby by the class decorator.
    
    Returns a unified list of all quibifiable attributes with their types, making it easier
    to handle different attribute types consistently.
    """
    attributes = []

    for name in dir(cls):
        # Skip magic methods (dunder methods)
        if name.startswith('__') and name.endswith('__'):
            continue

        # Determine attribute type and get the raw attribute from MRO
        attribute = _get_attribute_from_mro(cls, name)
        
        if is_property(cls, name):
            func_to_check = attribute.fget  # For properties, check the getter function
            wrapper_func = _wrap_property
        elif is_class_method(cls, name):
            func_to_check = attribute.__func__  # For class methods, check the underlying function
            wrapper_func = _wrap_classmethod
        elif is_regular_method(cls, name):
            func_to_check = attribute  # For instance methods, check the function directly
            wrapper_func = _wrap_instancemethod
        else:
            continue  # Skip attributes that don't match our types
        
        # Common check for all attribute types - check the function that will be wrapped
        if (not getattr(get_original_func(func_to_check), '__not_quiby__', False) and
            not is_quiby(func_to_check)):
            attributes.append(QuibifiableAttribute(name, attribute, wrapper_func))

    return attributes
