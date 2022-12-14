import time
import contextlib
from dataclasses import dataclass
from typing import Optional, Callable

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.env import DEBUG

from .logger import logger

TIMERS = {}


@dataclass
class TimerNotFoundException(PyQuibblerException):
    name: str

    def __str__(self):
        return self.name


@dataclass
class Timer:
    """
    Represents a single global timer,
    keeping track_and_handle_new_graphics of it's total time run and total amount of times run
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
        yield self
        current_total_time = time.time() - start_time

        self.total_time += current_total_time
        self.total_count += 1

        if callback is not None:
            callback(current_total_time)


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


@contextlib.contextmanager
def null_timer():
    yield


def timeit(name: str, message: Optional[str] = None):
    if not DEBUG:
        return null_timer()

    if message is None:
        return timer(name)

    return timer(name, lambda x: logger.info(f"{x * 1000:8.3f} ms -> " + message))
