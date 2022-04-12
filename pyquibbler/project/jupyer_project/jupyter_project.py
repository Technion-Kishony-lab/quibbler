import base64
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
from typing import Optional, Iterable, Tuple
from ipykernel.comm import Comm
from pyquibbler.file_syncing import ResponseToFileNotDefined
from pyquibbler.project import Project
from pyquibbler.project.jupyer_project.flask_dialog_server import run_flask_app


class JupyterProject(Project):
    def __init__(self, directory: Optional[Path], quib_weakrefs,
                 jupyter_notebook_path: Optional[Path] = None):
        super().__init__(directory, quib_weakrefs)
        self._jupyter_notebook_path = jupyter_notebook_path
        self._comm = None

    def _setup_tmp_project_directory_if_necessary(self):
        if self.directory is None:
            self.directory = tempfile.mkdtemp()
            with open(self._jupyter_notebook_path, 'r') as f:
                jupyter_notebook = json.load(f)
                b64_encoded_zip_content = jupyter_notebook['metadata'].get('quibs_archive')
                if not b64_encoded_zip_content:
                    return

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

    def _save_within_notebook(self):
        """
        Save the contents of the quibs within the actual notebook

        The current implementation is to zip the save directory and put the base64 encoded value in the notebooks
        metadata
        """
        self._setup_tmp_project_directory_if_necessary()
        super(JupyterProject, self).save_quibs(ResponseToFileNotDefined.WARN_IF_DATA)
        zip_buffer = self._create_zip_buffer_from_save_directory()

        with open(self._jupyter_notebook_path, 'r') as f:
            notebook_content = json.load(f)

        base64_bytes = base64.b64encode(zip_buffer.getvalue())
        base64_message = base64_bytes.decode('ascii')
        notebook_content['metadata']['quibs_archive'] = base64_message

        with open(self._jupyter_notebook_path, 'w') as f:
            f.write(json.dumps(notebook_content))

    def _load_quibs_from_notebook(self):
        self._setup_tmp_project_directory_if_necessary()
        super(JupyterProject, self).load_quibs(ResponseToFileNotDefined.WARN_IF_DATA)

    def _sync_with_notebook(self):
        self._setup_tmp_project_directory_if_necessary()
        super(JupyterProject, self).sync_quibs(ResponseToFileNotDefined.WARN_IF_DATA)

    def _cleanup(self):
        shutil.rmtree(self.directory)

    @staticmethod
    def _wrap_file_system_op(regular_func, within_notebook_func):

        def _func(in_notebook: bool):
            return within_notebook_func() if in_notebook else regular_func()

        return _func

    def listen_for_events(self):
        self._comm = Comm(target_name='pyquibbler')
        action_names_to_funcs = {
            "undo": self.undo,
            "redo": self.redo,
            "save": self._wrap_file_system_op(self.save_quibs, self._save_within_notebook),
            "load": self._wrap_file_system_op(self.load_quibs, self._load_quibs_from_notebook),
            "sync": self._wrap_file_system_op(self.sync_quibs, self._sync_with_notebook),
        }

        @self._comm.on_msg
        def _recv(msg):
            self._jupyter_notebook_path = ipynbname.path()
            data = msg['content']['data']
            func = action_names_to_funcs.get(data['action'])

            try:
                func(**msg['content']['data']['parameters'])
            except Exception as e:
                self._comm.send({"type": "dialog", "data": {"icon": "error", "title": "Oops...", "text": str(e)}})
                raise

    def text_dialog(self, title: str, message: str, buttons_and_options: Iterable[Tuple[str, str]]) -> str:
        answer_queue = multiprocessing.Queue()
        process = Process(target=run_flask_app, args=(answer_queue,))
        process.start()

        self._comm.send({"type": "requestDialog", "data": {"title": title,
                                                           "message": message,
                                                           "options": dict(buttons_and_options)}})

        return answer_queue.get(block=True)


def create_jupyter_project_if_in_jupyter_lab():
    project = JupyterProject.get_or_create()
    project.listen_for_events()
