import base64
import functools
import io
import json
import multiprocessing
import os
import shutil
import tempfile
import zipfile
from multiprocessing import Process

import ipynbname
from pathlib import Path
from typing import Optional, Iterable, Tuple, Callable, Union

from pyquibbler.utilities.warning_messages import no_header_warn
from pyquibbler.quib.quib import Quib
from pyquibbler.file_syncing import SaveFormat, ResponseToFileNotDefined
from pyquibbler.debug_utils.logger import logger
from pyquibbler.utilities.file_path import PathToNotebook

from ..project import Project
from .flask_dialog_server import run_flask_app
from .utils import is_within_jupyter_lab, find_free_port


class JupyterProject(Project):
    """
    Represents a project within a Jupyter Lab environment.

    On initialize_quibbler, if Python is running within a jupyter lab environment, the `current_project`
    will automatically be set to an instance of JupyterProject.

    JupyterProject is responsible for everything the normal project is, along with interfacing with the Quibbler
    extension of Jupyter lab.
    """

    def __init__(self, directory: Optional[Path], jupyter_notebook_path: Optional[Path] = None):
        super().__init__(directory)
        self._jupyter_notebook_path = jupyter_notebook_path
        self._tmp_save_directory = None
        self._should_save_load_within_notebook = True
        self._comm = None
        self._save_format = SaveFormat.TXT
        self._within_zip_and_send_context = False
        self.autoload_upon_first_get_value = True

    def _wrap_file_system_func(self, func: Callable,
                               save_and_send_after_op: bool = False,
                               skip_user_verification: bool = False,
                               ):
        """
        Wrap a file system function to do whatever is necessary before/after it.
        For example, if the save/load is within the jupyter notebook, make sure you open a tmp project directory for it
        You also need in certain situations to notify the client of the fs operation so it doesn't overwrite the changes
        """

        @functools.wraps(func)
        def _func(*args, **kwargs):
            if self._should_save_load_within_notebook:
                self._open_project_directory_from_notebook_zip()

            # If we're already within another wrapped file system func, we don't want to save data into notebook
            # and send the data to the client for this func
            zip_and_send = save_and_send_after_op and not self._within_zip_and_send_context

            if zip_and_send:
                self._within_zip_and_send_context = True

            if skip_user_verification and self._should_save_load_within_notebook:
                res = func(*args, **kwargs, skip_user_verification=True)
            else:
                res = func(*args, **kwargs)

            if zip_and_send:
                logger.info("Zipping and sending to client")
                self.zip_and_send_quibs_archive_to_client()
                self._within_zip_and_send_context = False

            return res

        return _func

    def save_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        return self._wrap_file_system_func(super(JupyterProject, self).save_quibs,
                                           save_and_send_after_op=True)(response_to_file_not_defined)

    def load_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        return self._wrap_file_system_func(super(JupyterProject, self).load_quibs)(response_to_file_not_defined)

    def sync_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        return self._wrap_file_system_func(super(JupyterProject, self).sync_quibs,
                                           save_and_send_after_op=True)(response_to_file_not_defined)

    def override_quib_persistence_functions(self):
        """
        Override quib persistence functions to ensure we save to notebook (or load from notebook) where necessary
        """
        Quib.save = self._wrap_file_system_func(Quib.save, skip_user_verification=True, save_and_send_after_op=True)
        Quib.load = self._wrap_file_system_func(Quib.load, skip_user_verification=True)
        Quib.sync = self._wrap_file_system_func(Quib.sync, save_and_send_after_op=True)

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

    def _open_project_directory_from_notebook_zip(self):
        """
        Open a project directory from the notebook's internal zip.
        The directory will be temporary, and will be deleted when the client calls "cleanup" (`_cleanup`)
        """
        notebook_content = self._get_notebook_content()
        if notebook_content is None:
            return

        if self._tmp_save_directory is None:
            self._tmp_save_directory = tempfile.mkdtemp()
        self._directory = PathToNotebook(self._tmp_save_directory)

        logger.info(f"Using notebook {self._jupyter_notebook_path}")
        logger.info(f"Loading quibs {self.directory}...")
        b64_encoded_zip_content = notebook_content['metadata'].get('quibs_archive')
        if b64_encoded_zip_content is not None:
            logger.info("Quibs exist! Unzipping quibs archive into directory...")
            raw_bytes = base64.b64decode(b64_encoded_zip_content)
            buffer = io.BytesIO(raw_bytes)
            zipfile.ZipFile(buffer).extractall(self.directory)

    def _create_zip_buffer_from_save_directory(self):
        """
        Create a buffer and write a zip file created from the project's save directory into it
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as archive:
            for root, _, files in os.walk(self.directory):
                for name in files:
                    path = os.path.join(root, name)
                    relative_path = os.path.join(os.path.relpath(root, self.directory), name)
                    archive.write(path, arcname=relative_path)
        return zip_buffer

    def zip_and_send_quibs_archive_to_client(self):
        """
        Send the quibs archive to the client- the client is responsible for writing it into the notebook.
        This needs to be called whenever there are changed to quib files (`_wrap_file_system_func` calls this func)
        """
        notebook_content = self._get_notebook_content()
        if notebook_content is None:
            return

        logger.info(f"Saving zip into notebook's metadata..., {self._directory}")
        zip_buffer = self._create_zip_buffer_from_save_directory()

        base64_bytes = base64.b64encode(zip_buffer.getvalue())
        base64_message = base64_bytes.decode('ascii')
        notebook_content['metadata']['quibs_archive'] = base64_message

        self._comm.send({"type": "quibsArchiveUpdate", "data": base64_message})

    def _cleanup(self):
        """
        Cleanup any temporary directories created for the JupyterProject (this should be called when the user finishes
        the session)
        """
        if self._tmp_save_directory is not None:
            shutil.rmtree(self._tmp_save_directory)

    def _clear_save_data(self):
        """
        Clear the saved quib data within the notebook
        """
        notebook_content = self._get_notebook_content()
        if notebook_content is None:
            return

        notebook_content['metadata']['quibs_archive'] = None

        with open(self._jupyter_notebook_path, 'w') as f:
            f.write(json.dumps(notebook_content, indent=2))

        if self._tmp_save_directory:
            shutil.rmtree(self._tmp_save_directory)
            os.makedirs(self._tmp_save_directory)

        for quib in self.quibs:
            if quib.assigned_name and quib.allow_overriding:
                quib.handler.file_syncer.on_data_changed()
                self.notify_of_overriding_changes(quib)

    def _set_should_save_load_within_notebook(self, should_save_load_within_notebook: bool):
        """
        When `True`, all save/loads will be kept within the notebook itself
        When `False`, the project will save to whichever directory it is specified to, without saving into the notebook
        """
        if self._should_save_load_within_notebook and not should_save_load_within_notebook:
            self._directory = None

        self._should_save_load_within_notebook = should_save_load_within_notebook

    def _refresh_jupyter_notebook_path(self):
        try:
            self._jupyter_notebook_path = ipynbname.path()
        except FileNotFoundError:
            self._jupyter_notebook_path = os.environ.get("JUPYTER_NOTEBOOK")
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
        # When we just wake up, we are not initially synchronized with the "SAve/Load inside notebook" state of the
        # client.
        self._call_client(action_type="getShouldSaveLoadWithinNotebook", message_data={})

    def set_undo_redo_buttons_enable_state(self):
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
        project.set_undo_redo_buttons_enable_state()

    return within_jupyter_lab
