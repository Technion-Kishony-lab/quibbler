from __future__ import annotations

from .project import Project, CannotLoadWithoutProjectPathException, CannotSaveWithoutProjectPathException, \
    NothingToUndoException, NothingToRedoException
from matplotlib.pyplot import figure
from matplotlib.widgets import Button

APP_TITLE = 'Data Quibbler'

class QuibApp:
    """
    An app to control quibbler project functionalities such as save/load undo/redo
    actions on many quibs
    """

    current_quibapp = None
    current_project = None

    def __init__(self):
        fig = figure(num=APP_TITLE, figsize=(1.7, 1))
        fig.canvas.mpl_connect('close_event', self.on_close)
        self.app_figure = fig

        H = 0.18 # button height
        W = 0.25 # Button width

        # Undo:
        self.undo_button = Button(ax=fig.add_axes([0.4, 0.7, W, H]), label='Undo')
        self.undo_button.on_clicked(self.undo)

        # Redo:
        self.redo_button = Button(ax=fig.add_axes([0.7, 0.7, W, H]), label='Redo')
        self.redo_button.on_clicked(self.redo)

        # Save:
        self.save_button = Button(ax=fig.add_axes([0.4, 0.2, W, H]), label='Save')
        self.save_button.on_clicked(self.save)

        # Load:
        self.load_button = Button(ax=fig.add_axes([0.7, 0.2, W, H]), label='Load')
        self.load_button.on_clicked(self.load)

    @classmethod
    def get_or_create(cls):
        if cls.current_quibapp is None:
            cls.current_project = Project.get_or_create()
            cls.current_quibapp = cls()
        return cls.current_quibapp

    @classmethod
    def on_close(cls,*args) -> None:
        cls.current_quibapp = None
        cls.current_project = None

    def undo(self, *args) -> None:
        try:
            self.current_project.undo()
        except NothingToUndoException:
            self.display_message(NothingToUndoException())

    def redo(self, *args) -> None:
        try:
            self.current_project.redo()
        except NothingToRedoException:
            self.display_message(NothingToRedoException())

    def save(self, *args) -> None:
        try:
            self.current_project.save_quibs()
        except CannotSaveWithoutProjectPathException:
            self.display_message(CannotSaveWithoutProjectPathException())

    def load(self, *args) -> None:
        try:
            self.current_project.load_quibs()
        except CannotLoadWithoutProjectPathException:
            self.display_message(CannotLoadWithoutProjectPathException())

    def display_message(self,msg):
        print(msg)