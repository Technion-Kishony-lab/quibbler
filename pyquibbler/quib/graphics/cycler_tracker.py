import functools
from dataclasses import dataclass

from matplotlib.axes import Axes
from matplotlib.axis import Axis


@dataclass
class TrackedCycle:

    cycled_list: list
    current_index: int


CYCLER_NAMES = [
    '_get_lines',
    '_get_patches_for_fill'
]


class CyclerTracker:

    def __init__(self, axes, cyclers_to_tracked_cycles=None):
        self._axes = axes
        self._cyclers_to_tracked_cycles = cyclers_to_tracked_cycles or {}

    @classmethod
    def get_or_create(cls, axes):
        self = cls(axes)
        for cycler_name in CYCLER_NAMES:
            cycler = getattr(axes, cycler_name)
            wrapped_cycler = self._create_cycler_wrapping_generator(cycler)
            setattr(axes, cycler_name, wrapped_cycler)
            axes._quibbler_cycler_tracker = self
        return self

    def reset(self):
        for cycler, tracked_cycles in self._cyclers_to_tracked_cycles.items():
            for tracked_cycle in tracked_cycles:
                tracked_cycle.current_index = 0

    def _create_cycler_wrapping_generator(self, original_cycler):

        def _wrapper(*_, **__):
            tracked_cycle = self._cyclers_to_tracked_cycles.setdefault(original_cycler,
                                                                       TrackedCycle(cycled_list=[], current_index=0))
            if tracked_cycle.current_index < len(tracked_cycle.cycled_list):
                next_item = tracked_cycle.cycled_list[tracked_cycle.current_index]
                tracked_cycle.current_index += 1
            else:
                next_item = next(original_cycler)
            yield next_item

        return _wrapper


def wrap_init(original_init):
    def _wrapper(self, *args, **kwargs):
        self = original_init(self, *args, **kwargs)
        self._context_saver = None
    return _wrapper


Axes.__init__ = wrap_init(Axes.__init__)
