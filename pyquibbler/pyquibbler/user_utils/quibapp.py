from __future__ import annotations

import matplotlib.pyplot as plt
from typing import Optional, Dict

from matplotlib.figure import Figure

from pyquibbler.project.project import Project, NothingToUndoException, NothingToRedoException, \
    NoProjectDirectoryException
from matplotlib.widgets import Button, TextBox
from pyquibbler.utilities.input_validation_utils import InvalidArgumentException
from functools import partial

APP_TITLE = 'Data Quibbler'


def figure_without_toolbar(*args, **kwargs):
    import matplotlib as mpl
    current_toolbar = mpl.rcParams['toolbar']
    mpl.rcParams['toolbar'] = 'None'
    fig = plt.figure(*args, **kwargs)
    mpl.rcParams['toolbar'] = current_toolbar
    return fig


def truncated_str(s: str, n: Optional[int] = None):
    return s if n is None or len(s) < n else '...' + s[-(n - 3):]


class QuibApp:
    """
    An app to control quibbler project functionalities such as save/load undo/redo
    actions on many quibs
    """

    current_quibapp: Optional[QuibApp] = None
    current_project: Optional[Project] = None

    def __init__(self):
        self.figure: Optional[Figure] = None
        self._buttons: Optional[Dict[str, Button]] = None
        self._path_text = None

    def create_app_figure(self):
        fig = figure_without_toolbar(num=APP_TITLE, figsize=(3.3, 1))
        fig.canvas.mpl_connect('close_event', self._on_figure_close)
        self.figure = fig

        h = 0.20  # button height
        w = 0.14  # Button width
        mh = 0.05  # left/right margin
        mv = 0.15  # distance from bottom/top
        spc = 0.03  # space between buttons
        mt = 0.22  # top margin

        # buttons:
        self._buttons = dict()
        self._buttons['undo'] = Button(ax=fig.add_axes([mh, mv, w, h]), label='Undo')
        self._buttons['redo'] = Button(ax=fig.add_axes([mh + w + spc, mv, w, h]), label='Redo')
        self._buttons['save'] = Button(ax=fig.add_axes([1 - mh - w - 2 * (spc + w), mv, w, h]), label='Save')
        self._buttons['load'] = Button(ax=fig.add_axes([1 - mh - w - 1 * (spc + w), mv, w, h]), label='Load')
        self._buttons['sync'] = Button(ax=fig.add_axes([1 - mh - w - 0 * (spc + w), mv, w, h]), label='Sync')

        project = self.current_project
        buttons_funcs_exceptions = (
            ('undo', project.undo, NothingToUndoException),
            ('redo', project.redo, NothingToRedoException),
            ('save', project.save_quibs, NoProjectDirectoryException),
            ('load', project.load_quibs, NoProjectDirectoryException),
            ('sync', project.sync_quibs, NoProjectDirectoryException),
        )
        for button, func, exception in buttons_funcs_exceptions:
            call_func = partial(self.on_button_click, project_func=func, exception=exception)
            self._buttons[button].on_clicked(call_func)

        # path:
        ax = fig.add_axes([mh, 1 - mt - h, 1 - 2 * mh, h])
        self._path_text = TextBox(ax=ax, label='', initial=self._get_project_path_str())
        self._path_text.active = False
        self._path_text.on_submit(self._set_path)
        self.current_project.on_path_change = self._handle_path_change
        ax.text(0, 1.1, 'path:', va='bottom', ha='left')

    def _get_project_path_str(self):
        return '' if self.current_project.directory is None else str(self.current_project.directory)

    def _set_path(self, path):
        try:
            self.current_project.path = path
        except InvalidArgumentException:
            pass

    def _handle_path_change(self, path):
        self._path_text.set_val(truncated_str(self._get_project_path_str(), 38))

    @classmethod
    def get_or_create(cls):
        if cls.current_quibapp is None:
            cls.current_project = Project.get_or_create()
            cls.current_quibapp = cls()
            cls.current_quibapp.create_app_figure()
        return cls.current_quibapp

    @classmethod
    def close(cls):
        current_quibapp = cls.current_quibapp
        if current_quibapp is not None:
            plt.close(current_quibapp.figure)
            cls.current_project = None
            cls.current_quibapp = None

    @classmethod
    def _on_figure_close(cls, *args) -> None:
        cls.current_quibapp = None
        cls.current_project.on_path_change = None
        cls.current_project = None

    @classmethod
    def on_button_click(cls, *args, project_func, exception) -> bool:
        try:
            project_func()
        except exception as e:
            cls._display_message(str(e))

    @classmethod
    def _display_message(cls, msg):
        print(msg)
