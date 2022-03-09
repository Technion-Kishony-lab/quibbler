import pathlib


class PathWithHyperLink(type(pathlib.Path())):
    def _repr_html_(self):
        return f'<a href="{self}">{self.name}</a>'
