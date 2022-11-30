from typing import Callable, Any, Set, List, Optional, Iterable

from matplotlib.axes import Axes
from matplotlib.widgets import AxesWidget

from pyquibbler.utilities.general_utils import Args, Kwargs
from pyquibbler.assignment import AssignmentToQuib, create_assignment, Assignment, get_override_group_for_quib_changes
from pyquibbler.path.path_component import Path
from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.quib.graphics.event_handling.canvas_event_handler import graphics_assignment_mode
from pyquibbler.quib.graphics.redraw import end_dragging


class WidgetQuibFuncCall(CachedQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        """
        The name of the widget attribute that is controlled by the widget.
        """
        return None

    def _connect_callbacks(self, widget: AxesWidget):
        """
        Add any logic here for connecting callbacks to your widget
        """
        pass

    def _get_axis(self) -> Axes:
        return self.func_args_kwargs.get('ax')

    def _set_rightclick_callback(self, widget: AxesWidget):
        self._get_axis()._quibbler_on_rightclick = self._on_right_click

    def _on_right_click(self, _mouse_event):
        ctrl = self.func_args_kwargs.get(self._get_control_variable())
        if isinstance(ctrl, Quib):
            changes = [AssignmentToQuib(ctrl, Assignment.create_default([]))]
        elif isinstance(ctrl, Iterable):
            changes = []
            for sub_ctrl in ctrl:
                if isinstance(sub_ctrl, Quib):
                    changes.append(AssignmentToQuib(sub_ctrl, Assignment.create_default([])))
        else:
            return

        self._inverse_assign_multiple_quibs(changes)

    def _inverse_assign(self, quib: Quib, path: Path, value: Any, tolerance: Any = None, on_drag: bool = False):
        assignment = create_assignment(value, path, tolerance)
        self._inverse_assign_multiple_quibs([AssignmentToQuib(quib, assignment)], on_drag)

    def _inverse_assign_multiple_quibs(self, quib_changes: List[AssignmentToQuib], on_drag: bool = False):
        with graphics_assignment_mode(self._get_axis()):
            get_override_group_for_quib_changes(quib_changes).apply(is_dragging=on_drag)

    def _on_release(self, *_, **__):
        end_dragging()

    def _run_single_call(self, func: Callable, graphics_collection: GraphicsCollection,
                         args: Args, kwargs: Kwargs, quibs_allowed_to_access: Set[Quib]):
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
            self._set_rightclick_callback(res)

        return res
