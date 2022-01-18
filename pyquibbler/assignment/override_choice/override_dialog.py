from __future__ import annotations
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from typing import List, Callable, Optional, TYPE_CHECKING
from enum import Enum

from pyquibbler.logger import logger
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utils import Flag, Mutable

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

UNSET = object()


@dataclass
class AssignmentCancelledByUserException(PyQuibblerException):
    pass


class OverrideChoiceType(Enum):
    OVERRIDE = 0
    DIVERGE = 1


@dataclass
class OverrideChoice:
    """
    Result of a choice between possible overrides.
    """
    choice_type: OverrideChoiceType
    chosen_index: Optional[int] = None

    def __post_init__(self):
        if self.choice_type is OverrideChoiceType.OVERRIDE:
            assert self.chosen_index is not None


def create_button(ax: Axes, label: str, callback: Callable[[], None]) -> Button:
    button = Button(ax, label)
    button.on_clicked(lambda _event: callback())
    return button


def show_fig(fig, choice_type):
    """
    Show fig until it is closed or choice_type is set.
    Return True if the figure was closed and False otherwise.
    """
    figure_closed = Flag(False)
    fig.canvas.mpl_connect('close_event', lambda _event: figure_closed.set(True))

    while choice_type.val is UNSET and not figure_closed:
        try:
            plt.pause(0.05)
        except Exception as e:
            logger.warning(f"Error in plt.pause: {e}")
            # This throws a TclError on windows with tkinter backend when the figure is closed
            break
    return figure_closed.val


def choose_override_dialog(options: List[Quib], can_diverge: bool) -> OverrideChoice:
    """
    Open a popup dialog to offer the user a choice between override options.
    If can_diverge is true, offer the user to diverge the override instead of choosing an override option.
    """
    from pyquibbler.graphics.widgets import QRadioButtons
    # Used to keep references to the widgets so they won't be garbage collected
    widgets = []
    axeses = []
    fig = plt.gcf()  # TODO: use figure the drag event was fired in

    background_ax = fig.add_axes([0, 0, 1, 1])
    background_ax.tick_params(left=False, right=False, labelleft=False, labelbottom=False, bottom=False)
    axeses.append(background_ax)

    grid = fig.add_gridspec(6, 6, left=0.1, right=0.9, bottom=0.1, top=0.9)
    radio_ax = fig.add_subplot(grid[:-1, :])
    radio_ax.axis("off")
    radio = QRadioButtons(radio_ax, [f'Override {quib.pretty_repr()}' for quib in options])
    widgets.append(radio)  # This is not strictly needed but left here to prevent a bug
    axeses.append(radio_ax)

    choice_type = Mutable(UNSET)
    button_specs = [('Cancel', None),
                    ('Override', OverrideChoiceType.OVERRIDE)]
    if can_diverge:
        button_specs.append(('Diverge', OverrideChoiceType.DIVERGE))

    for i, (label, button_choice) in enumerate(button_specs):
        ax = fig.add_subplot(grid[-1, -i - 1])
        button = create_button(ax, label, partial(choice_type.set, button_choice))
        widgets.append(button)
        axeses.append(ax)

    figure_closed = show_fig(fig, choice_type)
    if figure_closed:
        choice_type.set(None)
    else:
        for axes in axeses:
            axes.remove()
        fig.canvas.draw()

    if choice_type.val is None:
        raise AssignmentCancelledByUserException()
    return OverrideChoice(choice_type.val, radio.selected_index)
