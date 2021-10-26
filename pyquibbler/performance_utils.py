import contextlib
import time
from dataclasses import dataclass
from typing import Callable, Optional

from pyquibbler.exceptions import PyQuibblerException

TIMERS = {}


@dataclass
class TimerNotFoundException(PyQuibblerException):
    name: str


@dataclass
class Timer:
    """
    Represents a single global timer, keeping track of it's total time run and total amount of times run
    """

    name: str
    total_time: int = 0
    total_count: int = 0

    def __repr__(self):
        return f"<{self.__class__.__name__} - (tot: {self.total_time}s, " \
               f"count: {self.total_count}, " \
               f"t/c {self.total_time / self.total_count}s)>"

    @contextlib.contextmanager
    def timing(self, callback: Optional[Callable] = None):
        """
        Returns a context manager that will time whatever is ran within it
        """
        start_time = time.time()
        yield
        end_time = time.time() - start_time

        self.total_time += end_time
        self.total_count += 1

        if callback is not None:
            callback(end_time)


def get_timer(name: str) -> Timer:
    """
    Gets the corresponding `Timer` for a given name
    """
    if name not in TIMERS:
        raise TimerNotFoundException(name)
    return TIMERS[name]


def timer(name: str, callback: Optional[Callable] = None):
    """
    Returns a context manager in which you can time something under the given timer name.
    You can than retrieve the ran timer with `get_timer(name)`
    """
    if name in TIMERS:
        return TIMERS[name].timing(callback=callback)
    new_timer = Timer(name=name)
    TIMERS[name] = new_timer
    return new_timer.timing(callback=callback)
