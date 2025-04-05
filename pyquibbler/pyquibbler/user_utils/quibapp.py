from __future__ import annotations

import matplotlib.pyplot as plt
from typing import Optional, Dict
from matplotlib.figure import Figure
from matplotlib.widgets import Button
from functools import partial

from pyquibbler.project.project import Project, NothingToUndoException, NothingToRedoException, \
    NoProjectDirectoryException

APP_TITLE = 'Data Quibbler'


def figure_without_toolbar(*args, **kwargs):
    import matplotlib as mpl
    current_toolbar = mpl.rcParams['toolbar']
    mpl.rcParams['toolbar'] = 'None'
    fig = plt.figure(*args, **kwargs)
    mpl.rcParams['toolbar'] = current_toolbar
    return fig


class ColorButton(Button):
    # Class-level color variables.
    active_face_color = '#bbbbbb'
    inactive_face_color = '#ffffff'
    active_text_color = '#000000'
    inactive_text_color = '#888888'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active = True

    def set_active(self, active: bool):
        self._active = active
        super().set_active(active)
        # Set face and text colors based on active state.
        self.ax.set_facecolor(
            self.active_face_color if active else self.inactive_face_color
        )
        self.label.set_color(
            self.active_text_color if active else self.inactive_text_color
        )
        self.ax.figure.canvas.draw_idle()

    def draw(self, renderer):
        self.label.set_color(
            self.active_text_color if self._active else self.inactive_text_color
        )
        super().draw(renderer)


class QuibApp:
    current_quibapp: Optional[QuibApp] = None

    def __new__(cls, *args, **kwargs):
        if cls.current_quibapp is None:
            cls.current_quibapp = super(QuibApp, cls).__new__(cls)
        return cls.current_quibapp

    def __init__(self):
        # Prevent reinitialization on subsequent instantiation attempts.
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.figure: Optional[Figure] = None
        self._buttons: Dict[str, Button] = {}
        self.project = Project.get_or_create()

        self.create_app_figure()

    @classmethod
    def get_or_create(cls) -> QuibApp:
        """
        Get the current instance of QuibApp or create a new one if it doesn't exist.
        """
        if cls.current_quibapp is None:
            cls.current_quibapp = cls()
        return cls.current_quibapp

    def create_app_figure(self):
        fig = figure_without_toolbar(num=APP_TITLE, figsize=(3.3, 0.5))
        fig.canvas.mpl_connect('close_event', self._on_figure_close)
        self.figure = fig

        # Layout parameters
        h = 0.46  # button height
        w = 0.14  # button width
        mh = 0.05  # margin (left/right)
        mv = 0.2  # margin (bottom/top)
        spc = 0.03  # space between buttons

        # Create buttons and assign to the buttons dict
        self._buttons['undo'] = ColorButton(ax=fig.add_axes([mh, mv, w, h]), label='Undo')
        self._buttons['redo'] = ColorButton(ax=fig.add_axes([mh + w + spc, mv, w, h]), label='Redo')
        self._buttons['save'] = ColorButton(ax=fig.add_axes([1 - mh - w - 2 * (spc + w), mv, w, h]), label='Save')
        self._buttons['load'] = ColorButton(ax=fig.add_axes([1 - mh - w - 1 * (spc + w), mv, w, h]), label='Load')
        self._buttons['sync'] = ColorButton(ax=fig.add_axes([1 - mh - w, mv, w, h]), label='Sync')

        # Map button actions to project functions and handle expected exceptions
        button_actions = [
            ('undo', self.project.undo, NothingToUndoException),
            ('redo', self.project.redo, NothingToRedoException),
            ('save', self.project.save_quibs, NoProjectDirectoryException),
            ('load', self.project.load_quibs, NoProjectDirectoryException),
            ('sync', self.project.sync_quibs, NoProjectDirectoryException),
        ]

        for key, func, exception in button_actions:
            callback = partial(self.on_button_click, project_func=func, exception=exception)
            self._buttons[key].on_clicked(callback)
            self._buttons[key].set_active(True)

        self._update_undo_redo_enabled()
        self.project.add_undo_redo_callback(self._update_undo_redo_enabled)

    def _on_figure_close(self, event):
        self.close()

    def on_button_click(self, event, project_func, exception):
        try:
            project_func()
        except exception as e:
            self._display_message(str(e))

    def _display_message(self, msg: str):
        print(msg)

    def _update_undo_redo_enabled(self):
        if not self._buttons:
            return
        self._buttons['undo'].set_active(self.project.can_undo())
        self._buttons['redo'].set_active(self.project.can_redo())

    def close(self):
        if self.figure:
            plt.close(self.figure)
        self.figure = None
        if self.current_quibapp is self:
            self.current_quibapp = None
            self.project.remove_undo_redo_callback(self._update_undo_redo_enabled)

            type(self).current_quibapp = None
