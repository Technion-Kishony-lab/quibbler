import matplotlib.pyplot as plt
from time import sleep
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.widgets import RadioButtons, Button
from typing import List, Callable, Tuple
from enum import Enum

from pyquibbler.quib.assignment import QuibWithAssignment


class MyRadioButtons(RadioButtons):
    def __init__(self, ax, labels, active=0):
        super().__init__(ax, labels, active=active)
        self.selected_index = active

    def set_active(self, index):
        self.selected_index = index
        super().set_active(index)


class OverrideChoice(Enum):
    CANCEL = 0
    OVERRIDE = 1
    DIVERGE = 2


@dataclass
class Flag:
    is_set: bool = False

    def set(self):
        self.is_set = True

    def __bool__(self):
        return self.is_set


def create_button(ax: Axes, label: str, callback: Callable[[Event], None]):
    button = Button(ax, label)
    button.on_clicked(callback)
    return button


def show_fig(fig):
    closed = Flag()
    fig.canvas.mpl_connect('close_event', lambda _event: closed.set())
    fig.show()

    while not closed:
        # plt.pause blocks forever on tkinter backend, so we implement
        if fig.canvas.figure.stale:
            fig.canvas.draw_idle()
        plt.show(block=False)
        fig.canvas.flush_events()
        sleep(0.01)


def choose_override_dialog(options: List[QuibWithAssignment],
                           can_diverge: bool) -> Tuple[OverrideChoice, QuibWithAssignment]:
    # Used to keep references to the widgets so they won't be garbage collected
    widgets = []
    fig = plt.figure()
    grid = fig.add_gridspec(6, 6)

    radio_ax = fig.add_subplot(grid[:-1, :])
    radio = MyRadioButtons(radio_ax, [f'Override {option.quib}' for option in options])
    widgets.append(radio)  # This is not strictly needed but left here to prevent a bug

    choice = OverrideChoice.CANCEL

    def button_callback(button_choice, _event):
        nonlocal choice
        choice = button_choice
        plt.close(fig)

    button_specs = [('Cancel', OverrideChoice.CANCEL),
                    ('Override', OverrideChoice.CANCEL)]
    if can_diverge:
        button_specs.append(('Diverge', OverrideChoice.DIVERGE))

    for i, (label, choice) in enumerate(button_specs):
        ax = fig.add_subplot(grid[-1, -i - 1])
        button = create_button(ax, label, partial(button_callback, choice))
        widgets.append(button)

    show_fig(fig)
    return choice, options[radio.selected_index]
