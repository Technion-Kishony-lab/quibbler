from dataclasses import dataclass
from typing import Optional


@dataclass
class FileAndLineNumber:
    """
    Points to a specific line number within a specified file.
    """

    file_path: str
    line_no: Optional[int]

    def __repr__(self):
        return f'file: {self.file_path}, line={self.line_no}'

    def _repr_html_(self):
        return f'<a href="file://{self.file_path}">{self}</a>'
