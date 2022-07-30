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
from typing import Optional, Iterable, Tuple, Callable, Dict

from IPython import get_ipython
from ipykernel.comm import Comm

from pyquibbler import Quib
from pyquibbler.assignment import Overrider
from pyquibbler.file_syncing import SaveFormat, ResponseToFileNotDefined
from pyquibbler.logger import logger
from pyquibbler.path.path_component import set_path_indexed_classes_from_quib
from pyquibbler.project import Project
from pyquibbler.project.jupyer_project.exceptions import NoQuibFoundException
from pyquibbler.project.jupyer_project.flask_dialog_server import run_flask_app
from pyquibbler.project.jupyer_project.utils import is_within_jupyter_lab, find_free_port, get_serialized_quib
from pyquibbler.utilities.file_path import PathToNotebook


class JupyterProject(Project):
    """
    Represents a project within a Jupyer Lab environment.

    On initialize_quibbler, if Python is running within a jupyter lab environment, the `current_project`
    will automatically be set to an instance of JupterProject.

    JupyterProject is responsible for everything the normal project is, along with interfacing with the Quibbler
    extension of Jupyter lab.
    """

    def __init__(self, directory: Optional[Path], quib_weakrefs,
                 jupyter_notebook_path: Optional[Path] = None):
        super().__init__(directory, quib_weakrefs)
        self._jupyter_notebook_path = jupyter_notebook_path
        self._tmp_save_directory = None
        self._should_save_load_within_notebook = True
        self._comm = None
        self._tracked_quibs = {}
        self._last_requested_execution_count = 0
        self._save_format = SaveFormat.TXT
        self._within_zip_and_send_context = False
        self._should_notify_client_of_quib_changes = True
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

    def register_quib(self, quib: Quib):
        super(JupyterProject, self).register_quib(quib)
        self._tracked_quibs.setdefault(get_ipython().execution_count, []).append(quib)

    def _open_project_directory_from_notebook_zip(self):
        """
        Open a project directory from the notebook's internal zip.
        The directory will be temporary, and will be deleted when the client calls "cleanup" (`_cleanup`)
        """
        if self._tmp_save_directory is None:
            self._tmp_save_directory = tempfile.mkdtemp()

        self._directory = PathToNotebook(self._tmp_save_directory)

        logger.info(f"Using notebook {self._jupyter_notebook_path}")
        logger.info(f"Loading quibs {self.directory}...")
        with open(self._jupyter_notebook_path, 'r') as f:
            jupyter_notebook = json.load(f)
            b64_encoded_zip_content = jupyter_notebook['metadata'].get('quibs_archive')
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
        logger.info(f"Saving zip into notebook's metadata..., {self._directory}")
        zip_buffer = self._create_zip_buffer_from_save_directory()

        with open(self._jupyter_notebook_path, 'r') as f:
            notebook_content = json.load(f)

        base64_bytes = base64.b64encode(zip_buffer.getvalue())
        base64_message = base64_bytes.decode('ascii')
        notebook_content['metadata']['quibs_archive'] = base64_message

        self._comm.send({"type": "quibsArchiveUpdate", "data": base64_message})

    def _get_loaded_tracked_quibs(self, execution_count: int):
        """
        Get all quibs that can be overriden from frontend
        (both allow_overriding and have assigned_name) tracked during running of cells, loaded
        """
        if execution_count not in self._tracked_quibs:
            return {
                "quibs": []
            }

        tracked_quibs = self._tracked_quibs.pop(execution_count)
        quibs_to_send = [quib for quib in tracked_quibs if quib.assigned_name and quib.allow_overriding]

        try:
            self._should_notify_client_of_quib_changes = False
            for quib in quibs_to_send:
                quib.load()
        finally:
            self._should_notify_client_of_quib_changes = True

        dumped_quibs = {
            "quibs": [
                get_serialized_quib(quib)
                for quib in quibs_to_send
            ]
        }
        return dumped_quibs

    def _load_quib(self, quib_id: int):
        """
        Load a quib with a given id (this is python's object id)
        """
        quib = self._find_quib_by_id(quib_id)
        quib.load()
        logger.info(f"Loading quib {quib.name}, override count {len(quib.handler.overrider)}")
        return get_serialized_quib(quib)

    def _find_quib_by_id(self, quib_id: int) -> Quib:
        """
        Fina a quib with a given id (this is python's object id)
        """
        for quib_ref in self._quib_weakrefs:
            quib = quib_ref()
            if quib is not None and id(quib) == quib_id:
                return quib
        raise NoQuibFoundException(quib_id)

    def _save_quib(self, quib_id: int):
        """
        Save the quib to file.
        Note that we don't need to ensure this is saved to the notebook, as `Quib.save` is already wrapped to save to
        notebook when applicable
        """
        found_quib = self._find_quib_by_id(quib_id)
        found_quib.save()

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
        with open(self._jupyter_notebook_path, 'r') as f:
            notebook_content = json.load(f)
            notebook_content['metadata']['quibs_archive'] = None

        with open(self._jupyter_notebook_path, 'w') as f:
            f.write(json.dumps(notebook_content, indent=2))

        if self._tmp_save_directory:
            shutil.rmtree(self._tmp_save_directory)
            os.makedirs(self._tmp_save_directory)

        for quib_ref in self._quib_weakrefs:
            quib = quib_ref()
            if quib is not None and quib.assigned_name and quib.allow_overriding:
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

    def _upsert_assignment(self, quib_id: int, index: int, raw_override: Dict):
        """
        Upsert (update or insert) an assignment at a given index of a quib's overridden assignments.
        Note that we need to ensure this action can be "undone"
        """
        override_text = ""
        left = raw_override['left']
        right = raw_override['right']
        if left == '' or left.isspace():
            override_text += f"quib.assign({right})"
        else:
            override_text += f"quib{left} = {right}"
        overrider = Overrider()
        overrider.load_from_assignment_text(override_text)
        assignment = overrider[0]

        quib = self._find_quib_by_id(quib_id)
        self.push_single_assignment_to_undo_stack(
            quib=quib,
            assignment=assignment,
            assignment_index=index
        )
        if len(quib.handler.overrider) > index:
            quib.handler.overrider.pop_assignment_at_index(index)
        quib.handler.overrider.insert_assignment_at_index(assignment, index)
        quib.handler.file_syncer.on_data_changed()
        set_path_indexed_classes_from_quib(assignment.path, quib)

        quib.handler.invalidate_and_aggregate_redraw_at_path(assignment.path)

        return get_serialized_quib(quib)

    def _remove_assignment_with_quib_id_at_index(self, quib_id: int, index: int):
        quib = self._find_quib_by_id(quib_id)
        if index < len(quib.handler.overrider):
            self.remove_assignment_from_quib(quib, index)
        return get_serialized_quib(quib)

    def listen_for_events(self):
        """
        Listen for all events from frontend- this will create a callback for any event coming from the frontend,
        and will run the relevant method for the event.
        It will then send BACK the response with the `request_id` specificed in the original event
        """
        self._jupyter_notebook_path = os.environ.get("JUPYTER_NOTEBOOK", ipynbname.path())
        self._comm = Comm(target_name='pyquibbler')
        action_names_to_funcs = {
            "undo": self.undo,
            "redo": self.redo,
            "save": self.save_quibs,
            "load": self.load_quibs,
            "sync": self.sync_quibs,
            "clearData": self._clear_save_data,
            "upsertAssignment": self._upsert_assignment,
            "removeAssignment": self._remove_assignment_with_quib_id_at_index,
            "loadedTrackedQuibs": self._get_loaded_tracked_quibs,
            "loadQuib": self._load_quib,
            "saveQuib": self._save_quib,
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

    def notify_of_overriding_changes(self, quib: Quib):
        # We need to notify the frontend if there was a change in a quib (this is not always called upon a change-
        # if the frontend initiated the change and JupyterProject is the one to handle it, we simply return the quib
        # so as not to cause races)
        if self._should_notify_client_of_quib_changes and quib.assigned_name:
            self._call_client(action_type="quibChange", message_data=get_serialized_quib(quib))

    def get_save_within_notebook_state(self):
        # When we just wake up, we are not initially synchronized with the "SAve/Load inside notebook" state of the
        # client.
        self._call_client(action_type="getShouldSaveLoadWithinNotebook", message_data={})

    def text_dialog(self, title: str, message: str, buttons_and_options: Iterable[Tuple[str, str]]) -> str:
        # Any text dialog needs to be send to the frontend as an alert
        answer_queue = multiprocessing.Queue()
        port = find_free_port()
        process = Process(target=run_flask_app, args=(port, answer_queue))
        process.start()

        self._comm.send({"type": "requestDialog", "data": {"title": title,
                                                           "message": message,
                                                           "options": dict(buttons_and_options),
                                                           "port": port}})

        return answer_queue.get(block=True)


def create_jupyter_project_if_in_jupyter_lab():
    if is_within_jupyter_lab():
        project = JupyterProject.get_or_create()
        project.override_quib_persistence_functions()
        project.listen_for_events()
        project.get_save_within_notebook_state()
