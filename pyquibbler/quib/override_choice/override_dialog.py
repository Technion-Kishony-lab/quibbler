import matplotlib.pyplot as plt
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
from matplotlib.widgets import RadioButtons, Button
from typing import List, Callable, Optional
from enum import Enum

from pyquibbler.quib.assignment import QuibWithAssignment
from pyquibbler.utils import Mutable, Flag

DIALOG_OPEN = Flag(False)


class MyRadioButtons(RadioButtons):
    """
    Radio buttons that expose the selected index
    """

    def __init__(self, ax, labels, active=0):
        super().__init__(ax, labels, active=active)
        self.selected_index = active

    def set_active(self, index):
        self.selected_index = index
        super().set_active(index)


class OverrideChoiceType(Enum):
    CANCEL = 0
    OVERRIDE = 1
    DIVERGE = 2


@dataclass
class OverrideChoice:
    """
    Result of a choice between possible overrides.
    """
    choice_type: OverrideChoiceType
    chosen_override: Optional[QuibWithAssignment] = None

    def __post_init__(self):
        if self.choice_type is OverrideChoiceType.OVERRIDE:
            assert self.chosen_override is not None


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

    while choice_type.val is None and not figure_closed:
        try:
            plt.pause(0.05)
        except Exception:
            # This throws a TclError on windows with tkinter backend when the figure is closed
            break
    return figure_closed.val


def choose_override_dialog(options: List[QuibWithAssignment], can_diverge: bool) -> OverrideChoice:
    """
    Open a popup dialog to offer the user a choice between override options.
    If can_diverge is true, offer the user to diverge the override instead of choosing an override option.
    """
    # Used to keep references to the widgets so they won't be garbage collected
    widgets = []
    axeses = []
    fig = plt.gcf()  # TODO: use figure the drag event was fired in
    grid = fig.add_gridspec(6, 6, left=0, right=1, bottom=0, top=1)

    background_ax = fig.add_subplot(grid[:, :])
    background_ax.tick_params(left=False, right=False, labelleft=False, labelbottom=False, bottom=False)
    axeses.append(background_ax)

    radio_ax = fig.add_subplot(grid[:-1, :])
    radio_ax.axis("off")
    radio = MyRadioButtons(radio_ax, [f'Override {option.quib.pretty_repr()}' for option in options])
    widgets.append(radio)  # This is not strictly needed but left here to prevent a bug
    axeses.append(radio_ax)

    choice_type = Mutable(None)
    button_specs = [('Cancel', OverrideChoiceType.CANCEL),
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
        choice_type.val = OverrideChoiceType.CANCEL
    else:
        for axes in axeses:
            axes.remove()
        plt.show(block=False)

    return OverrideChoice(choice_type.val, options[radio.selected_index])
