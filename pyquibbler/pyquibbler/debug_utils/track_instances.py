import functools
from weakref import ref
from typing import Type

TRACKED_CLASSES_TO_WEAKREFS = {}


def track_instances_of_class(cls: Type):
    """
    Track all instances of a class (weak pointers)
    """
    prev_init = cls.__init__

    @functools.wraps(prev_init)
    def _wrapped_init(self, *args, **kwargs):
        res = prev_init(self, *args, **kwargs)
        TRACKED_CLASSES_TO_WEAKREFS.setdefault(cls, set()).add(ref(self))
        return res

    cls.__init__ = _wrapped_init


def get_all_instances_in_tracked_class(cls: Type):
    """
    Get all the instances of a tracked class
    """
    return {inst() for inst in TRACKED_CLASSES_TO_WEAKREFS.get(cls, set()) if inst() is not None}
