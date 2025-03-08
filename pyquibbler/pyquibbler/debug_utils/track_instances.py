import contextlib
import functools
import gc
from weakref import WeakSet
from typing import Type


@contextlib.contextmanager
def track_instances_of_class(cls: Type, raise_if_any_left_alive=True):
    """
    Track all instances of a class (weak pointers)
    """
    prev_init = cls.__init__
    live_instances = WeakSet()

    @functools.wraps(prev_init)
    def _wrapped_init(self, *args, **kwargs):
        res = prev_init(self, *args, **kwargs)
        live_instances.add(self)
        return res

    cls.__init__ = _wrapped_init

    try:
        yield live_instances
    finally:
        gc.collect()
        cls.__init__ = prev_init
        if raise_if_any_left_alive and len(live_instances) > 0:
            raise ValueError(f"Found {len(live_instances)} instances of {cls} left alive")
