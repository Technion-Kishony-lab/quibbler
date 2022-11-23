from .quibapp import QuibApp


def quibapp():
    """
    Open the Quibbler App

    See Also
    --------
    Project
    """
    return QuibApp.get_or_create()
