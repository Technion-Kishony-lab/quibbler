import functools
import json
import multiprocessing
import os
import tempfile
from contextlib import contextmanager
from multiprocessing import Process

import ipynbname
from pathlib import Path
from typing import Optional, Iterable, Tuple, Callable, Union

from pyquibbler.utilities.warning_messages import no_header_warn
from pyquibbler.quib.quib import Quib
from pyquibbler.file_syncing import SaveFormat, ResponseToFileNotDefined
from pyquibbler.debug_utils.logger import logger
from pyquibbler.utilities.file_path import NotebookArchiveMirrorPath
from .archive_folder import folder_to_dict, folder_to_zip, dict_to_folder, zip_to_folder

from ..project import Project
from .flask_dialog_server import run_flask_app
from .utils import is_within_jupyter_lab, find_free_port


SERIALIZE_TO_JSON = True


class JupyterProject(Project):
    """
    Represents a project within a Jupyter Lab environment.

    On initialize_quibbler, if Python is running within a jupyter lab environment, the `current_project`
    will automatically be set to an instance of JupyterProject.

    JupyterProject is responsible for everything the normal project is, along with interfacing with the Quibbler
    extension of Jupyter lab.
    """
    DEFAULT_SAVE_FORMAT = SaveFormat.JSON

    def __init__(self, directory: Optional[Path], jupyter_notebook_path: Optional[Path] = None):
        super().__init__(directory)
        self._jupyter_notebook_path = jupyter_notebook_path
        self._directory = NotebookArchiveMirrorPath()
        self._comm = None
        self._within_zip_and_send_context = False

    @property
    def _should_save_load_within_notebook(self):
        return isinstance(self._directory, NotebookArchiveMirrorPath)

    def _wrap_file_system_func(self, func: Callable,
                               save_to_notebook_after_op: bool = False,
                               ):
        """
        Wrap a file system function to do whatever is necessary before/after it.
        For example, if the save/load is within the jupyter notebook, make sure you open a tmp project directory for it
        You also need in certain situations to notify the client of the fs operation so it doesn't overwrite the changes
        """

        @functools.wraps(func)
        def _func(*args, **kwargs):
            if not self._should_save_load_within_notebook:
                return func(*args, **kwargs)

            if kwargs.get('skip_user_verification', None) is None:
                kwargs['skip_user_verification'] = True

            with self._open_project_directory_from_notebook_metadata(save_to_notebook_after_op):
                return func(*args, **kwargs)

        return _func

    def save_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA, *,
                   skip_user_verification: bool = None):
        return self._wrap_file_system_func(super(JupyterProject, self).save_quibs, True)(
            response_to_file_not_defined, skip_user_verification=skip_user_verification)

    def load_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA, *,
                   skip_user_verification: bool = None):
        return self._wrap_file_system_func(super(JupyterProject, self).load_quibs, False)(
            response_to_file_not_defined, skip_user_verification=skip_user_verification)

    def sync_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA, *,
                   skip_user_verification: bool = None):
        return self._wrap_file_system_func(super(JupyterProject, self).sync_quibs, True)(
            response_to_file_not_defined, skip_user_verification=skip_user_verification)

    def override_quib_persistence_functions(self):
        """
        Override quib persistence functions to ensure we save to notebook (or load from notebook) where necessary
        """
        Quib.save = self._wrap_file_system_func(Quib.save, True)
        Quib.load = self._wrap_file_system_func(Quib.load, False)
        Quib.sync = self._wrap_file_system_func(Quib.sync, True)

    def _call_client(self, action_type: str, message_data):
        logger.info(f"Sending to client {action_type} {message_data}")
        self._comm.send({'type': action_type, "data": message_data})

    def _get_notebook_content(self):
        if self._jupyter_notebook_path is None:
            return None
        try:
            with open(self._jupyter_notebook_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self._jupyter_notebook_path = None
            return None

    @contextmanager
    def _open_project_directory_from_notebook_metadata(self, save_to_notebook_after_op: bool = True):
        """
        Open a project directory from the notebook's internal zip.
        The directory will be temporary, and will be deleted when the client calls "cleanup" (`_cleanup`)
        """
        notebook_content = self._get_notebook_content()
        if notebook_content is None or self._within_zip_and_send_context:
            yield
            return

        logger.info(f"Using notebook {self._jupyter_notebook_path}")
        logger.info(f"Loading quibs {self.directory}...")
        archive = notebook_content['metadata'].get('quibs_archive', {})

        with tempfile.TemporaryDirectory() as tmpdir:
            self._within_zip_and_send_context = True
            previous_directory = self._directory
            self._directory = NotebookArchiveMirrorPath(tmpdir)
            self._deserialize_save_directory(archive)
            try:
                yield
            finally:
                if save_to_notebook_after_op:
                    logger.info(f"Saving zip into notebook's metadata..., {tmpdir}")
                    archive = self._serialize_save_directory()
                    self._send_archive_to_notebook(archive)
                self._within_zip_and_send_context = False
                self._directory = previous_directory

    def _send_archive_to_notebook(self, archive):
        self._comm.send({"type": "quibsArchiveUpdate", "data": archive})

    def _serialize_save_directory(self):
        """
        Create a buffer and write a zip file created from the project's save directory into it
        """
        if SERIALIZE_TO_JSON:
            return folder_to_dict(self._directory)
        else:
            return folder_to_zip(self._directory)

    def _deserialize_save_directory(self, archive):
        if SERIALIZE_TO_JSON:
            dict_to_folder(archive, self._directory)
        else:
            zip_to_folder(archive, self._directory)

    def _cleanup(self):
        """
        Cleanup any temporary directories created for the JupyterProject (this should be called when the user finishes
        the session)
        """
        # nothing to do. temp folders are now created and destroyed per save/load operartion
        pass

    def _clear_save_data(self):
        """
        Clear the saved quib data within the notebook
        """
        self._send_archive_to_notebook({})

    def _set_should_save_load_within_notebook(self, should_save_load_within_notebook: bool):
        """
        When `True`, all save/loads will be kept within the notebook itself
        When `False`, the project will save to whichever directory it is specified to, without saving into the notebook
        """
        if should_save_load_within_notebook:
            self._directory = NotebookArchiveMirrorPath()
        else:
            self._directory = None

    def _refresh_jupyter_notebook_path(self):
        self._jupyter_notebook_path = os.environ.get("JUPYTER_NOTEBOOK_TEST")
        if self._jupyter_notebook_path is None:
            try:
                self._jupyter_notebook_path = ipynbname.path()
            except FileNotFoundError:
                pass
        if self._jupyter_notebook_path is None:
            no_header_warn(
                'ibynbname was unable to identify the filename of the Jupyter notebook.\n'
                'Saving quibs to Jupyter notebook is disabled.\n'
                'To enable saving quibs to Jupyter notebook, you can manually set the notebook file path, using:\n'
                '`qb.get_project().set_jupyter_notebook_path(...)`\n')

    def get_jupyter_notebook_path(self):
        """
        Returns the path of the Jupyter notebook.

        When working withing Jupyter lab, Quibbler can save quibs to the Jupyter notebook.
        The jupyter_notebook_path designates the location of the notebook.
        The path location is typically set automatically as the Notebook in which Quibbler is running.

        See Also
        --------
        set_jupyter_notebook_path
        """
        return self._jupyter_notebook_path

    def set_jupyter_notebook_path(self, path: Optional[Union[Path, str]]):
        """
        Set the file name of Jupyter notebook.

        When working withing Jupyter lab, Quibbler can save quibs to the Jupyter notebook.
        The jupyter_notebook_path designates the location of the notebook.
        The path location is typically set automatically as the Notebook in which Quibbler is running.
        If automatic setting fails, you can use set_jupyter_notebook_path to manually set the notebook path.

        Parameters
        ----------
        path: str or Path
            Absolute or relative path to the Jupyter notebook.

        See Also
        --------
        get_jupyter_notebook_path
        """
        if isinstance(path, str):
            path = Path(path)
        path = path.resolve()
        if path.suffix != '.ipynb':
            raise ValueError('jupyter_notebook_path must be set to a valid Jupyter file with extension ".ipynb"')
        if not path.exists():
            raise ValueError('Notebook file not found.')
        self._jupyter_notebook_path = path

    def listen_for_events(self):
        """
        Listen for all events from frontend- this will create a callback for any event coming from the frontend,
        and will run the relevant method for the event.
        It will then send BACK the response with the `request_id` specified in the original event
        """

        from pyquibbler.optional_packages.get_IPython import Comm

        self._refresh_jupyter_notebook_path()
        self._comm = Comm(target_name='pyquibbler')
        action_names_to_funcs = {
            "undo": self.undo,
            "redo": self.redo,
            "save": self.save_quibs,
            "load": self.load_quibs,
            "sync": self.sync_quibs,
            "clearData": self._clear_save_data,
            "setShouldSaveLoadWithinNotebook": self._set_should_save_load_within_notebook,
            "cleanup": self._cleanup,
        }

        @self._comm.on_msg
        def _recv(msg):
            data = msg['content']['data']
            func = action_names_to_funcs.get(data['action'])
            request_id = data['requestId']

            try:
                res = func(**data['parameters'])
            except Exception as e:
                self._comm.send({"type": "error", 'data': str(e), "requestId": request_id})
                raise
            else:
                self._comm.send({'type': "response", "data": res, "requestId": request_id})

    def get_save_within_notebook_state(self):
        # When we just wake up, we are not initially synchronized with the "Save/Load inside notebook" state of the
        # client.
        self._call_client(action_type="getShouldSaveLoadWithinNotebook", message_data={})

    def _on_undo_redo_change(self):
        super()._on_undo_redo_change()
        self._call_client(action_type="setUndoRedoButtons", message_data={'undoEnabled': str(self.can_undo()),
                                                                          'redoEnabled': str(self.can_redo()),
                                                                          })

    def text_dialog(self, title: str, message: str, buttons_and_options: Iterable[Tuple[str, str]]) -> str:
        # Any text dialog needs to be sent to the frontend as an alert
        answer_queue = multiprocessing.Queue()
        port = find_free_port()
        process = Process(target=run_flask_app, args=(port, answer_queue))
        process.start()

        self._comm.send({"type": "requestDialog", "data": {"title": title,
                                                           "message": message,
                                                           "options": dict(buttons_and_options),
                                                           "port": port}})

        return answer_queue.get(block=True)


def create_jupyter_project_if_in_jupyter_lab() -> bool:
    within_jupyter_lab = is_within_jupyter_lab()
    if within_jupyter_lab:
        project = JupyterProject.get_or_create()
        project.override_quib_persistence_functions()
        project.listen_for_events()
        project.get_save_within_notebook_state()
        project._on_undo_redo_change()

    return within_jupyter_lab
