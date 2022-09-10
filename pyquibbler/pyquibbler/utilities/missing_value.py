from pyquibbler.utilities.basic_types import Singleton


class Missing(Singleton):
    """
    Designates a missing value in a function call
    """

    def __repr__(self):
        return 'missing'


missing = Missing()
