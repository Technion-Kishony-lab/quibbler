from matplotlib import get_backend
from pyquibbler.utilities.general_utils import Args, Kwargs


def prevent_squash(args: Args, kwargs: Kwargs):
    obj = args[0]
    return not (obj.created_in_get_value_context and get_backend() == 'TkAgg')
