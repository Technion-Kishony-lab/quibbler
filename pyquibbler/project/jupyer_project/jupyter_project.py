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
from typing import Optional, Iterable, Tuple, Callable

from IPython import get_ipython
from ipykernel.comm import Comm

from pyquibbler import Quib
from pyquibbler.file_syncing import SaveFormat, ResponseToFileNotDefined
from pyquibbler.logger import logger
from pyquibbler.project import Project
from pyquibbler.project.jupyer_project.flask_dialog_server import run_flask_app
from pyquibbler.project.jupyer_project.utils import is_within_jupyter_lab, find_free_port, get_serialized_quib


class JupyterProject(Project):
    def __init__(self, directory: Optional[Path], quib_weakrefs,
                 jupyter_notebook_path: Optional[Path] = None):
        super().__init__(directory, quib_weakrefs)
        self._jupyter_notebook_path = jupyter_notebook_path
        self._tmp_save_directory = None
        self._should_save_load_within_notebook = True
        self._comm = None
        self._tracked_quibs_stack = []
        self._last_requested_execution_count = 0
        self._save_format = SaveFormat.TXT
        self._within_zip_and_send_context = False

    def _wrap_file_system_func(self, func: Callable, save_and_send_after_op: bool = False):
        """
        Wrap a file system function to do whatever is necessary before/after it.
        For example, if the save/load is within the jupyter notebook, make sure you open a tmp project directory for it
        You also need in certain situations to notify the client of the fs operation so it doesn't overwrite the changes
        """
        @functools.wraps(func)
        def _func(*args, **kwargs):
            if self._should_save_load_within_notebook:
                self._open_project_directory_from_zip()
            elif self.directory is None or str(self.directory) == str(self._tmp_save_directory):
                raise Exception("No directory has been set")

            # If we're already within another wrapped file system func, we don't want to save data into notebook
            # and send the data to the client for this func
            zip_and_send = save_and_send_after_op and not self._within_zip_and_send_context

            if zip_and_send:
                self._within_zip_and_send_context = True

            res = func(*args, **kwargs)

            if zip_and_send:
                logger.info("Zipping and sending to client")
                self.save_directory_into_notebook_and_send_quib_metadata_to_client()
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

    def override_quib_functions(self):
        Quib.save = self._wrap_file_system_func(Quib.save, save_and_send_after_op=True)
        Quib.load = self._wrap_file_system_func(Quib.load)
        Quib.sync = self._wrap_file_system_func(Quib.sync, save_and_send_after_op=True)

    def _call_client(self, action_type: str, message_data):
        logger.info(f"Sending to client {action_type} {message_data}")
        self._comm.send({'type': action_type, "data": message_data})

    def register_quib(self, quib: Quib):
        super(JupyterProject, self).register_quib(quib)

        if quib.assigned_name and quib.allow_overriding:
            execution_count_diff = get_ipython().execution_count - self._last_requested_execution_count
            quib_lists_to_add = execution_count_diff - len(self._tracked_quibs_stack)

            logger.info(f"quib lists to add, {quib_lists_to_add}")

            for i in range(quib_lists_to_add):
                self._tracked_quibs_stack.append([])

            current_quibs_list = self._tracked_quibs_stack[-1]
            current_quibs_list.append(quib)

    def _open_project_directory_from_zip(self):
        if self._tmp_save_directory is not None:
            self._directory = self._tmp_save_directory
            return

        self._directory = self._tmp_save_directory = tempfile.mkdtemp()

        logger.info(f"Using notebook {self._jupyter_notebook_path}")
        logger.info(f"Loading quibs {self.directory}...")
        with open(self._jupyter_notebook_path, 'r') as f:
            jupyter_notebook = json.load(f)
            b64_encoded_zip_content = jupyter_notebook['metadata'].get('quibs_archive')
            if b64_encoded_zip_content is not None:
                logger.info("Quibs exist! Unziping quibs archive into directory...")
                raw_bytes = base64.b64decode(b64_encoded_zip_content)
                buffer = io.BytesIO(raw_bytes)
                zipfile.ZipFile(buffer).extractall(self.directory)

    def _create_zip_buffer_from_save_directory(self):
        """
        Create a buffer and write a zip file created from the save directory into it
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as archive:
            for root, _, files in os.walk(self.directory):
                for name in files:
                    path = os.path.join(root, name)
                    relative_path = os.path.join(os.path.relpath(root, self.directory), name)
                    archive.write(path, arcname=relative_path)
        return zip_buffer

    def save_directory_into_notebook_and_send_quib_metadata_to_client(self):
        logger.info(f"Saving zip into notebook's metadata..., {self._directory}")
        zip_buffer = self._create_zip_buffer_from_save_directory()

        with open(self._jupyter_notebook_path, 'r') as f:
            notebook_content = json.load(f)

        base64_bytes = base64.b64encode(zip_buffer.getvalue())
        base64_message = base64_bytes.decode('ascii')
        notebook_content['metadata']['quibs_archive'] = base64_message

        with open(self._jupyter_notebook_path, 'w') as f:
            f.write(json.dumps(notebook_content, indent=2))

        self._comm.send({"type": "quibsArchiveUpdate", "data": base64_message})

    def _send_tracked_quibs(self):
        self._last_requested_execution_count = get_ipython().execution_count - 1
        if len(self._tracked_quibs_stack) == 0:
            return {
                "quibs": []
            }

        logger.info(f"Last requested execution count, {self._last_requested_execution_count}")
        tracked_quibs = self._tracked_quibs_stack.pop(0)
        names_to_quibs = {
            quib.assigned_name: quib
            for quib in tracked_quibs
        }
        dumped_quibs = {
            "quibs": [
                get_serialized_quib(quib)
                for quib in names_to_quibs.values()
            ]
        }
        return dumped_quibs

    def _load_quib(self, quib_name: str):
        quib = self._find_quib_by_name(quib_name)
        quib.load()
        return get_serialized_quib(quib)

    def _find_quib_by_name(self, quib_name: str) -> Quib:
        for quib_ref in self._quib_weakrefs:
            quib = quib_ref()
            if quib is not None and quib.assigned_name == quib_name:
                return quib
        raise Exception("Quib is probably garbage disposed")

    def _save_quib(self, quib_name: str):
        found_quib = self._find_quib_by_name(quib_name)
        found_quib.save()

    def _cleanup(self):
        if self._tmp_save_directory is not None:
            shutil.rmtree(self._tmp_save_directory)

    def _change_quib(self, name: str, overrides):
        override_text = ""
        for override in overrides:
            if override['left'] == 'quib':
                override_text += f"quib.assign({override['right']})"
            else:
                override_text += f"{override['left']} = {override['right']}\n"

        quib = self._find_quib_by_name(name)
        quib.handler.overrider.load_from_assignment_text(override_text)
        quib.handler.file_syncer.on_data_changed()
        quib.handler.invalidate_and_redraw_at_path([])

    def _clear_save_data(self):
        with open(self._jupyter_notebook_path, 'r') as f:
            notebook_content = json.load(f)
            notebook_content['metadata']['quibs_archive'] = None

        with open(self._jupyter_notebook_path, 'w') as f:
            f.write(json.dumps(notebook_content, indent=2))

        for quib_ref in self._quib_weakrefs:
            quib = quib_ref()
            if quib is not None and quib.assigned_name and quib.allow_overriding:
                quib.handler.file_syncer.on_data_changed()
                self.notify_of_overriding_changes(quib)

    def _toggle_should_save_load_within_notebook(self, should_save_load_within_notebook: bool):
        self._should_save_load_within_notebook = should_save_load_within_notebook

    def listen_for_events(self):
        self._jupyter_notebook_path = ipynbname.path()
        self._comm = Comm(target_name='pyquibbler')
        action_names_to_funcs = {
            "undo": self.undo,
            "redo": self.redo,
            "save": self.save_quibs,
            "load": self.load_quibs,
            "sync": self.sync_quibs,
            "clearData": self._clear_save_data,
            "trackedQuibs": self._send_tracked_quibs,
            "loadQuib": self._load_quib,
            "saveQuib": self._save_quib,
            "changeQuib": self._change_quib,
            "setShouldSaveLoadWithinNotebook": self._toggle_should_save_load_within_notebook,
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
        if quib.assigned_name:
            self._call_client(action_type="quibChange", message_data=get_serialized_quib(quib))

    def text_dialog(self, title: str, message: str, buttons_and_options: Iterable[Tuple[str, str]]) -> str:
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
        project.override_quib_functions()
        project.listen_for_events()
