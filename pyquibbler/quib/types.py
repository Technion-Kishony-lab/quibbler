from dataclasses import dataclass
from typing import Optional


@dataclass
class FileAndLineNumber:
    file_path: str
    line_no: Optional[int]

    def __repr__(self):
        return f'file: {self.file_path}, line={self.line_no}'

    def _repr_html_(self):
        return f'<a href="file://{self.file_path}">{self}</a>'
