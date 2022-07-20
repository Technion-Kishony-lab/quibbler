from __future__ import annotations
import contextlib
from typing import Set
from matplotlib.axes import Axes
from matplotlib.pyplot import fignum_exists

from pyquibbler.logger import logger
from pyquibbler.utilities.performance_utils import timer
from pyquibbler.cache.cache import CacheStatus
from pyquibbler.quib.quib import Quib


QUIBS_TO_REDRAW: Set[Quib] = set()
QUIBS_TO_NOTIFY_OVERRIDING_CHANGES: Set[Quib] = set()
IN_AGGREGATE_REDRAW_MODE = False


@contextlib.contextmanager
def aggregate_redraw_mode():
    """
    In aggregate redraw mode, no axeses will be redrawn until the end of the context manager (unless force=True
    was used when redrawing)
    """
    global IN_AGGREGATE_REDRAW_MODE
    if IN_AGGREGATE_REDRAW_MODE:
        yield
    else:
        IN_AGGREGATE_REDRAW_MODE = True
        try:
            yield
        finally:
            IN_AGGREGATE_REDRAW_MODE = False
        _redraw_quibs_with_graphics()
        _notify_of_overriding_changes()


def _redraw_quibs_with_graphics():
    quibs_that_are_invalid = [quib for quib in QUIBS_TO_REDRAW if quib.cache_status != CacheStatus.ALL_VALID]
    with timer("quib redraw", lambda x: logger.info(f"redrawing {len(quibs_that_are_invalid)} quibs: {x}s")):
        for quib in quibs_that_are_invalid:
            quib.handler.redraw_if_appropriate()

    axeses = {axes
              for quib in quibs_that_are_invalid for axes in quib.handler.get_axeses()}

    redraw_axeses(axeses)
    QUIBS_TO_REDRAW.clear()


def _notify_of_overriding_changes():
    with timer("override notify", lambda x: logger.info(f"notifying overriding changes for "
                                                        f"{len(QUIBS_TO_NOTIFY_OVERRIDING_CHANGES)} quibs: {x}s")):
        from pyquibbler import Project
        project = Project.get_or_create()
        for quib in QUIBS_TO_NOTIFY_OVERRIDING_CHANGES:
            project.notify_of_overriding_changes(quib)

    QUIBS_TO_NOTIFY_OVERRIDING_CHANGES.clear()


def redraw_quibs_with_graphics_or_add_in_aggregate_mode(quibs: Set[Quib]):
    global QUIBS_TO_REDRAW
    QUIBS_TO_REDRAW |= quibs
    if not IN_AGGREGATE_REDRAW_MODE:
        _redraw_quibs_with_graphics()


def notify_of_overriding_changes_or_add_in_aggregate_mode(quib: Quib):
    global QUIBS_TO_NOTIFY_OVERRIDING_CHANGES
    QUIBS_TO_NOTIFY_OVERRIDING_CHANGES.add(quib)
    if not IN_AGGREGATE_REDRAW_MODE:
        _notify_of_overriding_changes()


def redraw_axeses(axeses: Set[Axes]):
    """
    Actual redrawing of axes- this should be WITHOUT rendering anything except for the new artists
    """
    canvases = {axes.figure.canvas for axes in axeses if fignum_exists(axes.figure.number)}
    with timer("redraw", lambda x: logger.info(f"redraw {len(axeses)} axeses, {len(canvases)} canvases {x}s")):
        for canvas in canvases:
            canvas.draw()
