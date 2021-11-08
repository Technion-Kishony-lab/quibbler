from pyquibbler.exceptions import PyQuibblerException


class QuibCallFailedException(PyQuibblerException):

    def __init__(self, quibs, exception):
        self.quibs = quibs
        self.exception = exception

    def __str__(self):
        quib_reprs = list(map(repr, self.quibs))
        quibs_formatted = ""
        indent_level = "  "
        for quib_repr in quib_reprs[::-1]:
            quibs_formatted += "\n" + indent_level + quib_repr
            indent_level += "  "
        last_quib = self.quibs[-1]
        return f"Failed to execute {last_quib}, " \
               f"the following quibs were in the stack of the exception: {quibs_formatted} failed with:\n{type(self.exception).__name__}: {self.exception}"

