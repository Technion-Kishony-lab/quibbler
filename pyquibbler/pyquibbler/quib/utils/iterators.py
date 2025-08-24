from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_recursively


def iter_quibs_in_object(obj, recurse_mode='deep', iterate_on_object_arrays=True, iterate_on_attributes=False):
    from pyquibbler.quib.quib import Quib
    yield from iter_objects_of_type_in_object_recursively(
        Quib, obj, recurse_mode=recurse_mode,
        iterate_on_object_arrays=iterate_on_object_arrays,
        iterate_on_attributes=iterate_on_attributes)
