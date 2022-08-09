from typing import Callable, Tuple, Any, Mapping, Set, List

from matplotlib.axes import Axes
from matplotlib.widgets import AxesWidget

from pyquibbler.assignment.assignment import AssignmentToQuib, create_assignment
from pyquibbler.assignment.override_choice import get_override_group_for_quib_changes
from pyquibbler.path.path_component import Path
from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.quib import Quib
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.quib.graphics.event_handling.canvas_event_handler import graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import end_dragging


class WidgetQuibFuncCall(CachedQuibFuncCall):

    def _connect_callbacks(self, widget: AxesWidget):
        """
        Add any logic here for connecting callbacks to your widget
        """
        pass

    def _get_axis(self) -> Axes:
        return self.func_args_kwargs.get('ax')

    def _inverse_assign(self, quib: Quib, path: Path, value: Any, tolerance: Any = None, on_drag: bool = False):

        assignment = create_assignment(value, path, tolerance)
        self._inverse_assign_multiple_quibs([AssignmentToQuib(quib, assignment)], on_drag)

    def _inverse_assign_multiple_quibs(self, quib_changes: List[AssignmentToQuib], on_drag: bool = False):
        with graphics_assignment_mode(self._get_axis()):
            get_override_group_for_quib_changes(quib_changes).apply(is_dragging=on_drag)

    def _on_release(self, *_, **__):
        end_dragging()

    def _run_single_call(self, func: Callable, graphics_collection: GraphicsCollection,
                         args: Tuple[Any, ...], kwargs: Mapping[str, Any], quibs_allowed_to_access: Set[Quib]):
        previous_widgets = graphics_collection.widgets
        res = super(WidgetQuibFuncCall, self)._run_single_call(func, graphics_collection, args, kwargs,
                                                               quibs_allowed_to_access)

        # We don't want to recreate the widget every time (and re-add callbacks)- if we already had a widget, just
        # return that
        if len(previous_widgets) > 0 and isinstance(res, AxesWidget):
            assert len(previous_widgets) == 1
            res = list(previous_widgets)[0]
        else:
            # This widget never existed- we're creating it for the first time, so we need to connect callbacks
            self._connect_callbacks(res)

        return res
