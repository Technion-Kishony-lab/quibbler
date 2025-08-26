from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_recursively, is_iterator_empty


def iter_quibs_in_object(obj, recurse_mode='deep', max_depth_on_object_arrays=-1, max_depth_on_attributes=-1):
    from pyquibbler.quib.quib import Quib
    yield from iter_objects_of_type_in_object_recursively(
        Quib, obj, recurse_mode=recurse_mode,
        max_depth_on_object_arrays=max_depth_on_object_arrays,
        max_depth_on_attributes=max_depth_on_attributes)


def is_there_a_quib_in_object(obj) -> bool:
    """
    Returns true if there is a quib object nested inside the given object.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj))
