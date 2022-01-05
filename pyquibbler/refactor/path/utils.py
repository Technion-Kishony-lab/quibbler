from pyquibbler.refactor.path import Path


def get_nd_working_component_value_from_path(path: Path, raise_on_empty_path: bool = False):
    """
    Get the first working component value you can from the path- this will always be entirely "squashed", so you will
    get a component that expresses everything possible before needing to go another step "deeper" in

    If no component is found (path is empty), the path expresses getting "everything"- so we give a true value
    """
    return path[0].component if len(path) > 0 else True


def working_component(path: Path):
    return path[0].component if len(path) > 0 else True


def path_beyond_working_component(path: Path):
    return path[1:]