from itertools import chain


def is_iterator_empty(iterator):
    """
    Check if a given iterator is empty by getting one item from it.
    Note that this item will be lost!
    """
    try:
        next(iterator)
        return False
    except StopIteration:
        return True


def deep_copy_and_replace_quibs_with_vals(obj):
    """
    Returns an iterator for all quib objects nested in the given python object.
    """
    from pyquibbler.quib import Quib
    if isinstance(obj, Quib):
        return obj.get_value()
    elif isinstance(obj, (tuple, list, set)):
        return type(obj)(deep_copy_and_replace_quibs_with_vals(sub_obj) for sub_obj in obj)
    elif isinstance(obj, slice):
        return slice(deep_copy_and_replace_quibs_with_vals(obj.start),
                     deep_copy_and_replace_quibs_with_vals(obj.stop),
                     deep_copy_and_replace_quibs_with_vals(obj.step))
    return obj


def iter_quibs_in_object(obj):
    """
    Returns an iterator for all quib objects nested in the given python object.
    Quibs that appear more than once will not be repeated.
    """
    from pyquibbler.quib import Quib
    quibs = set()
    if isinstance(obj, Quib):
        if obj not in quibs:
            quibs.add(obj)
            yield obj
    elif isinstance(obj, (tuple, list, set)):
        for sub_obj in obj:
            yield from iter_quibs_in_object(sub_obj)


def iter_quibs_in_args(args, kwargs):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    return iter_quibs_in_object(list(chain(args, kwargs.values())))


def call_func_with_quib_values(func, args, kwargs):
    """
    Calls a function with the specified args and kwargs while replacing quibs with their values.
    """
    new_args = [deep_copy_and_replace_quibs_with_vals(arg) for arg in args]
    kwargs = {name: deep_copy_and_replace_quibs_with_vals(val) for name, val in kwargs.items()}
    return func(*new_args, **kwargs)


def call_method_with_quib_values(func, self, args, kwargs):
    """
    Calls an instance method with the specified args and kwargs while replacing quibs with their values.
    """
    return call_func_with_quib_values(func, [self, *args], kwargs)


def is_there_a_quib_in_object(obj):
    """
    Returns true if there is a quib object nested inside the given object and false otherwise.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj))


def is_there_a_quib_in_args(args, kwargs):
    """
    Returns true if there is a quib object nested inside the given args and kwargs and false otherwise.
    For use by function wrappers that need to determine if the underlying function was called with a quib.
    """
    return not is_iterator_empty(iter_quibs_in_args(args, kwargs))
