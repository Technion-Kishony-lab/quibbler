from __future__ import annotations

import matplotlib.pyplot as plt
from typing import Optional
from pyquibbler.project.project import Project, NothingToUndoException, NothingToRedoException, \
    NoProjectDirectoryException
from matplotlib.widgets import Button, TextBox
from pyquibbler.utilities.input_validation_utils import InvalidArgumentException

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
        fig = figure_without_toolbar(num=APP_TITLE, figsize=(3.3, 1))
        fig.canvas.mpl_connect('close_event', self._on_figure_close)
        self.app_figure = fig

        h = 0.20  # button height
        w = 0.14  # Button width
        mh = 0.05  # left/right margin
        mv = 0.15  # distance from bottom/top
        spc = 0.03  # space between buttons
        mt = 0.22  # top margin

        # Undo:
        self._undo_button = Button(ax=fig.add_axes([mh, mv, w, h]), label='Undo')
        self._undo_button.on_clicked(self.undo)

        # Redo:
        self._redo_button = Button(ax=fig.add_axes([mh + w + spc, mv, w, h]), label='Redo')
        self._redo_button.on_clicked(self.redo)

        # Save:
        self._save_button = Button(ax=fig.add_axes([1 - mh - w - 2 * (spc + w), mv, w, h]), label='Save')
        self._save_button.on_clicked(self.save)

        # Load:
        self._load_button = Button(ax=fig.add_axes([1 - mh - w - 1 * (spc + w), mv, w, h]), label='Load')
        self._load_button.on_clicked(self.load)

        # Sync:
        self._sync_button = Button(ax=fig.add_axes([1 - mh - w - 0 * (spc + w), mv, w, h]), label='Sync')
        self._sync_button.on_clicked(self.sync)

        # path:
        axs = fig.add_axes([mh, 1 - mt - h, 1 - 2 * mh, h])
        self._path_text = TextBox(ax=axs, label='', initial=self._get_project_path_str())
        self._path_text.active = False
        self._path_text.on_submit(self._set_path)
        self.current_project.on_path_change = self._handle_path_change
        axs.text(0, 1.1, 'path:', va='bottom', ha='left')

        # path:
        # axs = fig.add_axes([mh, 1 - mt - h, 1 - 2 * mh, h])
        # self._path_text = axs.text(0, 0.5, self._get_project_path_str(), va='center', ha='left')
        # axs.set_visible(False)
        # self.current_project.on_path_change = self._handle_path_change

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
        return cls.current_quibapp

    @classmethod
    def close(cls):
        current_quibapp = cls.current_quibapp
        if current_quibapp is not None:
            plt.close(current_quibapp.app_figure)
            cls.current_project = None
            cls.current_quibapp = None

    @classmethod
    def _on_figure_close(cls, *args) -> None:
        cls.current_quibapp = None
        cls.current_project.on_path_change = None
        cls.current_project = None

    def undo(self, *args) -> None:
        try:
            self.current_project.undo()
        except NothingToUndoException:
            self._display_message(NothingToUndoException())

    def redo(self, *args) -> None:
        try:
            self.current_project.redo()
        except NothingToRedoException:
            self._display_message(NothingToRedoException())

    def save(self, *args) -> None:
        try:
            self.current_project.save_quibs()
        except NoProjectDirectoryException as e:
            self._display_message(str(e))

    def load(self, *args) -> None:
        try:
            self.current_project.load_quibs()
        except NoProjectDirectoryException as e:
            self._display_message(str(e))

    def sync(self, *args) -> None:
        try:
            self.current_project.sync_quibs()
        except NoProjectDirectoryException as e:
            self._display_message(str(e))

    def _display_message(self, msg):
        print(msg)
