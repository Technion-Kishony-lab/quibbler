from typing import Any, Tuple, List


class Overrider:
    def __init__(self):
        self._overrides: List[Tuple[Any, Any]] = []

    def add_override(self, key: Any, value: Any):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._overrides.append((key, value))

    def override(self, data: Any):
        """
        Applies all overrides to the given data.
        """
        for key, value in self._overrides:
            data[key] = value
