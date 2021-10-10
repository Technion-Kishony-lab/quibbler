import functools
from dataclasses import dataclass
from typing import List, Iterable, Iterator
from matplotlib.axes import Axes


CYCLER_HOLDER_NAMES = [
    '_get_lines',
    '_get_patches_for_fill'
]


class TimeTravelingCycler:
    """
    A time traveling cycler both saves all items that came from a particular cycler, and then allows "going back in
    time" so as to recreate the cyclers history
    """

    def __init__(self, original_cycler: Iterator, cycled: List = None, current_index: int = 0):
        self._original_cycler = original_cycler
        self._cycled = cycled or []
        self._current_index = current_index

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_index < len(self._cycled):
            next_item = self._cycled[self._current_index]
        else:
            next_item = next(self._original_cycler)
            self._cycled.append(next_item)
        self._current_index += 1
        return next_item

    def reset(self):
        """
        Reset the current time traveling cycler to the beginning of time
        """
        self._current_index = 0


def set_time_traveling_cyclers_on_axes_prop_cyclers(axes: Axes):
    """
    Set all relevant time traveling cyclers on the given axes- this will keep track of all cyclers and allow via
    `reset_time_traveling_cyclers_on_axes`
    to go back to a previous time in the cycling
    """
    for cycler_holding_name in CYCLER_HOLDER_NAMES:
        current_cycler_holder = getattr(axes, cycler_holding_name)
        current_cycler_holder.prop_cycler = TimeTravelingCycler(
            original_cycler=current_cycler_holder.prop_cycler,
        )


def reset_time_traveling_cyclers_on_axes(axes: Axes):
    """
    Reset all time traveling cyclers on the given axes to the beginning of time- this will recreate the history
    """
    for cycler_holding_name in CYCLER_HOLDER_NAMES:
        current_cycler_holder = getattr(axes, cycler_holding_name)
        assert isinstance(current_cycler_holder.prop_cycler, TimeTravelingCycler)

        current_cycler_holder.reset()


def get_wrapped_init_to_add_time_traveling_cyclers(original_init):
    """
    Get a wrapped init that will set time traveling cyclers on the object created
    """
    def _wrapper(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        set_time_traveling_cyclers_on_axes_prop_cyclers(self)
    return _wrapper


def override_axes_init():
    Axes.__init__ = get_wrapped_init_to_add_time_traveling_cyclers(Axes.__init__)

