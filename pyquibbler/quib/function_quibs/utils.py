import matplotlib.pyplot as plt
from time import sleep
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.widgets import RadioButtons, Button
from typing import List, Optional, Callable
from enum import Enum

from ..assignment import QuibWithAssignment


class MyRadioButtons(RadioButtons):
    def __init__(self, ax, labels, active=0):
        super().__init__(ax, labels, active=active)
        self.selected_index = active

    def set_active(self, index):
        self.selected_index = index
        super().set_active(index)


class OverrideChoice(Enum):
    NONE = 0
    OVERRIDE = 1
    DIVERGE = 2


@dataclass
class Flag:
    is_set: bool = False

    def set(self):
        self.is_set = True

    def __bool__(self):
        return self.is_set


def button(ax: Axes, label: str, callback: Callable[[Event], None]):
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


def choose_override_dialog(options: List[QuibWithAssignment], can_diverge: bool) -> Optional[QuibWithAssignment]:
    fig = plt.figure()
    labels = [f'Override {option.quib}' for option in options]
    # Warning: don't lose the reference to the radio object or it will be garbage collected
    grid = fig.add_gridspec(5, 5)
    radio_ax = fig.add_subplot(grid[:-1, :])
    radio = MyRadioButtons(radio_ax, labels)
    choice = OverrideChoice.NONE

    def button_callback(button_choice, _event):
        nonlocal choice
        choice = button_choice
        plt.close(fig)

    override_button_ax = fig.add_subplot(grid[-1, -1])
    # Warning: don't lose the reference to the button or it will be garbage collected
    _override_button = button(override_button_ax, 'Override', partial(button_callback, OverrideChoice.OVERRIDE))
    if can_diverge:
        diverge_button_ax = fig.add_subplot(grid[-1, -2])
        # Warning: don't lose the reference to the button or it will be garbage collected
        _diverge_button = button(diverge_button_ax, 'Diverge', partial(button_callback, OverrideChoice.DIVERGE))
    show_fig(fig)
    assert choice is not OverrideChoice.NONE
    if choice is OverrideChoice.OVERRIDE:
        assert radio.selected_index is not None
        return options[radio.selected_index]
    return None
