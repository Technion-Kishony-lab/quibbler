from __future__ import annotations
import contextlib
from typing import Set, Dict, TYPE_CHECKING
from matplotlib.figure import Figure
from matplotlib.pyplot import fignum_exists
from matplotlib._pylab_helpers import Gcf

from pyquibbler.quib.graphics import GraphicsUpdateType
from pyquibbler.logger import logger
from pyquibbler.utilities.performance_utils import timer

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


QUIBS_TO_REDRAW: Dict[GraphicsUpdateType, Set[Quib]] = {GraphicsUpdateType.DRAG: set(), GraphicsUpdateType.DROP: set()}
QUIBS_TO_NOTIFY_OVERRIDING_CHANGES: Set[Quib] = set()
IN_AGGREGATE_REDRAW_MODE = False


@contextlib.contextmanager
def aggregate_redraw_mode(is_dragging: bool = False):
    """
    In aggregate redraw mode, no axeses will be redrawn until the end of the context manager
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
        _redraw_quibs_with_graphics(GraphicsUpdateType.DRAG)
        _notify_of_overriding_changes()
        if not is_dragging:
            end_dragging()


def end_dragging():
    from pyquibbler import Project
    _redraw_quibs_with_graphics(GraphicsUpdateType.DROP)
    Project.get_or_create().push_pending_undo_group_to_undo_stack()


@contextlib.contextmanager
def skip_canvas_draws(should_skip: bool = True):

    original_canvas_draw = None
    if should_skip:
        figure_managers = Gcf.get_all_fig_managers()
        if figure_managers:

            def _skip_draw(*args, **kwargs):
                return

            canvas_class = type(figure_managers[0].canvas)
            original_canvas_draw = canvas_class.draw
            canvas_class.draw = _skip_draw

    yield

    if original_canvas_draw is not None:
        canvas_class.draw = original_canvas_draw


def _redraw_quibs_with_graphics(graphics_update: GraphicsUpdateType):
    global QUIBS_TO_REDRAW
    quibs = QUIBS_TO_REDRAW[graphics_update]
    with timer("quib redraw", lambda x: logger.info(f"redrawing {len(quibs)} quibs: {x}s")), \
            skip_canvas_draws():
        for quib in quibs:
            quib.handler.reevaluate_graphic_quib()

    figures = {figure for quib in quibs for figure in quib.handler.get_figures() if figure is not None}

    redraw_figures(figures)
    quibs.clear()


def _notify_of_overriding_changes():
    with timer("override notify", lambda x: logger.info(f"notifying overriding changes for "
                                                        f"{len(QUIBS_TO_NOTIFY_OVERRIDING_CHANGES)} quibs: {x}s")):
        from pyquibbler import Project
        project = Project.get_or_create()
        for quib in QUIBS_TO_NOTIFY_OVERRIDING_CHANGES:
            project.notify_of_overriding_changes(quib)

    QUIBS_TO_NOTIFY_OVERRIDING_CHANGES.clear()


def redraw_quib_with_graphics_or_add_in_aggregate_mode(quib: Quib, graphics_update: GraphicsUpdateType):
    global QUIBS_TO_REDRAW
    if not (graphics_update == GraphicsUpdateType.DRAG or graphics_update == GraphicsUpdateType.DROP):
        return

    QUIBS_TO_REDRAW[graphics_update].add(quib)
    if not IN_AGGREGATE_REDRAW_MODE:
        _redraw_quibs_with_graphics(graphics_update)


def notify_of_overriding_changes_or_add_in_aggregate_mode(quib: Quib):
    global QUIBS_TO_NOTIFY_OVERRIDING_CHANGES
    QUIBS_TO_NOTIFY_OVERRIDING_CHANGES.add(quib)
    if not IN_AGGREGATE_REDRAW_MODE:
        _notify_of_overriding_changes()


def redraw_figures(figures: Set[Figure]):
    """
    Actual redrawing of figure- this should be WITHOUT rendering anything except for the new artists
    """
    canvases = {figure.canvas for figure in figures if fignum_exists(figure.number)}
    with timer("redraw", lambda x: logger.info(f"redraw {len(figures)} figures: {x}s")):
        for canvas in canvases:
            canvas.draw()
