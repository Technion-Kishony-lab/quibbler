from __future__ import annotations
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from typing import List, Callable, Optional, TYPE_CHECKING, Tuple
from enum import Enum

from pyquibbler.logger import logger
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utils import Flag, Mutable
from pyquibbler.env import OVERIDE_DIALOG_IN_SEPERATE_WINDOW, \
    OVERIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT, OVERIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

UNSET = object()


@dataclass
class AssignmentCancelledByUserException(PyQuibblerException):

    def __str__(self):
        return "User cancel inverse assignment dialog."


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


def add_axes_by_inches(fig, position):
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
    if invoking_axes is None and OVERIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT \
        or invoking_axes is not None and OVERIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT:
        choice_type, selected_index = choose_override_text_dialog(str_options, can_diverge)
    else:
        choice_type, selected_index = choose_override_graphics_dialog(str_options, can_diverge, invoking_axes)
    if choice_type is None:
        raise AssignmentCancelledByUserException()
    return OverrideChoice(choice_type, selected_index)


def choose_override_graphics_dialog(str_options: List[str],
                                    can_diverge: bool,
                                    invoking_axes: Optional[Axes]
                                    ) -> (Optional[OverrideChoiceType], int):

    # Used to keep references to the widgets so they won't be garbage collected
    widgets = []
    axeses = []

    is_new_figure = OVERIDE_DIALOG_IN_SEPERATE_WINDOW or invoking_axes is None
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
    widgets.append(radio)  # This is not strictly needed but left here to prevent a bug
    axeses.append(radio_ax)

    choice_type = Mutable(UNSET)
    button_specs = [('Cancel', None),
                    ('Override', OverrideChoiceType.OVERRIDE)]
    if can_diverge:
        button_specs.append(('Diverge', OverrideChoiceType.DIVERGE))

    for i, (label, button_choice) in enumerate(button_specs):
        ax = add_axes_by_inches(fig, [2 - i * 1.0 + 0.15 + shift[0], 0.1 + shift[1], 0.7, 0.3])
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
        if is_new_figure:
            plt.close(fig)
    return choice_type.val, radio.selected_index


def choose_override_text_dialog(str_options: List[str],
                                can_diverge: bool,
                                ) -> (Optional[OverrideChoiceType], int):

    print('Overriding choices:')
    if can_diverge:
        print(f'({0}) {"[Diverge]"}')
    for index, str_option in enumerate(str_options):
        print(f'({index + 1}) {str_option}')

    print('')
    selected_index = None
    choice_type = None
    choice = None
    while choice is None:
        choice = input('Choose the number of the quib to override \n(press enter without a choice to cancel): ')
        if len(choice) == 0:
            print('Cancel')
            break
        else:
            try:
                choice = int(choice)
            except ValueError:
                choice = None
            if choice == 0 and can_diverge:
                choice_type = OverrideChoiceType.DIVERGE
                print('Diverging...')
            elif 1 <= choice <= len(str_options):
                choice_type = OverrideChoiceType.OVERRIDE
                selected_index = choice - 1
                print('Overriding: ', str_options[selected_index])
            else:
                choice = None

    return choice_type, selected_index
