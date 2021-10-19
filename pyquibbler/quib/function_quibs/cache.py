from typing import List, Any

from pyquibbler.quib.assignment import PathComponent


class ShallowCache:

    def __init__(self, value: Any = None):
        self._value = value

    def set_valid_value_at_path_component(self, path_component: PathComponent, value: Any) -> None:
        pass

    def set_invalid_at_path_component(self, path_component: PathComponent) -> None:
        pass

    def is_valid_at_path_component(self, path_component: PathComponent) -> bool:
        pass

    def get_value_at_path_component(self, path_component: PathComponent) -> Any:
        pass

