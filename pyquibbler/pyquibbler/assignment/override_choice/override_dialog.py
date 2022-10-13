from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import List, Callable, Optional
from enum import Enum

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.widgets import Button

from pyquibbler.debug_utils.logger import logger
from pyquibbler.utilities.basic_types import Flag, Mutable
from pyquibbler.env import OVERRIDE_DIALOG_IN_SEPARATE_WINDOW, \
    OVERRIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT, OVERRIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT
from .exceptions import AssignmentCancelledByUserException

from typing import TYPE_CHECKING

from pyquibbler.project import Project

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib

UNSET = object()


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
            logger.warning(f"Error in plt.pause:\n{e}")
            # This throws a TclError on windows with tkinter backend when the figure is closed
            break
    return figure_closed.val


def add_axes_by_inches(fig, position) -> Axes:
    from mpl_toolkits.axes_grid1 import Divider, Size
    h = [Size.Fixed(position[0]), Size.Fixed(position[2])]
    v = [Size.Fixed(position[1]), Size.Fixed(position[3])]
    divider = Divider(fig, (0, 0, 1, 1), h, v, aspect=False)
    return fig.add_axes(divider.get_position(),
                        axes_locator=divider.new_locator(nx=1, ny=1))


def pretty_radio_buttons(fig, box, labels,
                         line_distance=0.3,
                         radius=0.08,
                         top_margin=0.2,
                         circle_x=0.2,
                         circle_text_distance=0.05,
                         color='grey',
                         ):
    # all dimensions in inches

    from pyquibbler.graphics.widgets import QRadioButtons
    from numpy import arange

    ax = add_axes_by_inches(fig, box)
    ax.axis([0, box[2], 0, box[3]])
    ax.axis("off")
    ax.transAxes = ax.transData
    radios = QRadioButtons(ax, labels, activecolor=color)

    n = len(labels)

    dy = min(line_distance, (box[3] - 2 * top_margin) / (n - 1))
    ys = box[3] - top_margin - arange(n) * dy

    for circle, label, y in zip(radios.circles, radios.labels, ys):
        circle.set_radius(radius)
        circle.set_center((circle_x, y))
        label.set_x(circle_x + radius + circle_text_distance)
        label.set_y(y)
    return ax, radios


def choose_override_dialog(options: List[Quib], can_diverge: bool) -> OverrideChoice:
    """
    Open a popup dialog to offer the user a choice between override options.
    If can_diverge is true, offer the user to diverge the override instead of choosing an override option.
    """

    from pyquibbler.quib.graphics.event_handling.canvas_event_handler import get_graphics_assignment_mode_axes

    invoking_axes = get_graphics_assignment_mode_axes()
    str_options = [quib.name for quib in options]
    if invoking_axes is None and OVERRIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT \
            or invoking_axes is not None and OVERRIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT:
        override_choice = choose_override_text_dialog(str_options, can_diverge)
    else:
        override_choice = choose_override_graphics_dialog(str_options, can_diverge, invoking_axes)
    if override_choice.choice_type is OverrideChoiceType.CANCEL:
        raise AssignmentCancelledByUserException()
    return override_choice


def choose_override_graphics_dialog(str_options: List[str],
                                    can_diverge: bool,
                                    invoking_axes: Optional[Axes]
                                    ) -> OverrideChoice:
    axeses = []
    buttons = []
    is_new_figure = OVERRIDE_DIALOG_IN_SEPARATE_WINDOW or invoking_axes is None
    if is_new_figure:
        fig = plt.figure(figsize=(3, 2.5))
        shift = (0, 0)
    else:
        fig = invoking_axes.figure
        shift = (0.5, 0.5)
        background_ax = add_axes_by_inches(fig, [shift[0], shift[1], 3, 2.5])
        background_ax.tick_params(left=False, right=False, labelleft=False, labelbottom=False, bottom=False)
        axeses.append(background_ax)

    radio_ax, radio = pretty_radio_buttons(fig, [0.2 + shift[0], 1 + shift[1], 2.6, 1.3], str_options)
    axeses.append(radio_ax)

    choice_type = Mutable(UNSET)
    button_specs = [('Cancel', OverrideChoiceType.CANCEL),
                    ('Override', OverrideChoiceType.OVERRIDE)]
    if can_diverge:
        button_specs.append(('Diverge', OverrideChoiceType.DIVERGE))

    for i, (label, button_choice) in enumerate(button_specs):
        ax = add_axes_by_inches(fig, [2 - i * 1.0 + 0.15 + shift[0], 0.1 + shift[1], 0.7, 0.3])
        button = create_button(ax, label, partial(choice_type.set, button_choice))
        axeses.append(ax)
        buttons.append(button)

    figure_closed = show_fig(fig, choice_type)
    if figure_closed:
        choice_type.set(OverrideChoiceType.CANCEL)
    else:
        for axes in axeses:
            axes.remove()
        fig.canvas.draw()
        if is_new_figure:
            plt.close(fig)
    if choice_type.val is OverrideChoiceType.OVERRIDE:
        return OverrideChoice(choice_type.val, radio.selected_index)
    return OverrideChoice(choice_type.val)


def choose_override_text_dialog(str_options: List[str],
                                can_diverge: bool,
                                ) -> OverrideChoice:

    buttons_to_str_and_choice = dict()
    for index, str_option in enumerate(str_options):
        buttons_to_str_and_choice[str(index + 1)] = \
            (str_option, OverrideChoice(OverrideChoiceType.OVERRIDE, index))

    if can_diverge:
        buttons_to_str_and_choice['D'] = ('[Diverge]', OverrideChoice(OverrideChoiceType.DIVERGE))

    buttons_to_str_and_choice['C'] = ('[Cancel]', OverrideChoice(OverrideChoiceType.CANCEL))

    selected_button = Project.get_or_create().text_dialog(
        title='Overriding choice',
        message='Choose the quib to override:',
        buttons_and_options={button: str_and_choice[0] for button, str_and_choice in buttons_to_str_and_choice.items()}
    )

    return buttons_to_str_and_choice[selected_button][1]
