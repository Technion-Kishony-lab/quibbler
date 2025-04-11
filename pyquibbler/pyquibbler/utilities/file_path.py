import pathlib


class PathWithHyperLink(type(pathlib.Path())):
    def _repr_html_(self):
        return f'<a href="file:///{self}">{self.name}</a>'


class NotebookArchiveMirrorPath(PathWithHyperLink):

    name = '[Save in notebook]'

    def _repr_html_(self):
        return self.name

    def __repr__(self):
        return self.name
