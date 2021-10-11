import matplotlib.pyplot as plt
from time import sleep
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.widgets import RadioButtons, Button
from typing import List, Callable, Optional
from enum import Enum

from pyquibbler.quib.assignment import QuibWithAssignment
from pyquibbler.utils import Flag


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


@dataclass()
class OverrideChoice:
    """
    Result of a choice between possible overrides.
    """
    choice_type: OverrideChoiceType
    chosen_override: Optional[QuibWithAssignment] = None

    def __post_init__(self):
        if self.choice_type is OverrideChoiceType.OVERRIDE:
            assert self.chosen_override is not None


def create_button(ax: Axes, label: str, callback: Callable[[Event], None]) -> Button:
    button = Button(ax, label)
    button.on_clicked(callback)
    return button


def show_fig(fig):
    """
    Show the given figure and wait until it is closed.
    """
    closed = Flag(False)
    fig.canvas.mpl_connect('close_event', lambda _event: closed.set(True))
    fig.show()
    while not closed:
        plt.pause(0.1)


def choose_override_dialog(options: List[QuibWithAssignment], can_diverge: bool) -> OverrideChoice:
    """
    Open a popup dialog to offer the user a choice between override options.
    If can_diverge is true, offer the user to diverge the override instead of choosing an override option.
    """
    # Used to keep references to the widgets so they won't be garbage collected
    widgets = []
    fig = plt.figure()
    grid = fig.add_gridspec(6, 6)

    radio_ax = fig.add_subplot(grid[:-1, :])
    radio = MyRadioButtons(radio_ax, [f'Override {option.quib.pretty_repr()}' for option in options])
    widgets.append(radio)  # This is not strictly needed but left here to prevent a bug

    choice_type = OverrideChoiceType.CANCEL

    def button_callback(button_choice: OverrideChoiceType, _event):
        nonlocal choice_type
        choice_type = button_choice
        plt.close(fig)

    button_specs = [('Cancel', OverrideChoiceType.CANCEL),
                    ('Override', OverrideChoiceType.OVERRIDE)]
    if can_diverge:
        button_specs.append(('Diverge', OverrideChoiceType.DIVERGE))

    for i, (label, button_choice) in enumerate(button_specs):
        ax = fig.add_subplot(grid[-1, -i - 1])
        button = create_button(ax, label, partial(button_callback, button_choice))
        widgets.append(button)

    show_fig(fig)
    return OverrideChoice(choice_type, options[radio.selected_index])
