import base64
import io
import zipfile
import os
import json


def walk_directory(directory):
    """
    Walk the directory and yield the files.
    """
    for root, _, files in os.walk(directory):
        for name in files:
            path = os.path.join(root, name)
            yield path


def folder_to_zip(directory):
    """
    Serialize the contents of a directory to a base64-encoded zip string.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as archive:
        for path in walk_directory(directory):
            relative_path = os.path.relpath(path, directory)
            archive.write(path, arcname=relative_path)

    base64_bytes = base64.b64encode(zip_buffer.getvalue())
    return base64_bytes.decode('ascii')


def folder_to_dict(folder):
    """
    Serialize the contents of a folder to a JSON string.
    """
    data = {}
    for path in walk_directory(folder):
        relative_path = os.path.relpath(path, folder)
        with open(path, 'r') as f:
            content = f.read()
        is_json = path.endswith('json')
        if is_json:
            content = json.loads(content)
        data[relative_path] = content

    return data


def zip_to_folder(zip, directory):
    raw_bytes = base64.b64decode(zip)
    buffer = io.BytesIO(raw_bytes)
    zipfile.ZipFile(buffer).extractall(directory)


def dict_to_folder(data, directory):
    if not data:
        return
    for path, content in data.items():
        if isinstance(content, dict):
            content = json.dumps(content)
        full_path = os.path.join(directory, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
