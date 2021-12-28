from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, Type, Tuple

import numpy as np

from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from pyquibbler.quib.graphics.graphics_function_quib import create_array_from_func
from pyquibbler.refactor.graphics.graphics_collection import GraphicsCollection
from pyquibbler.refactor.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.refactor.overriding import CannotFindDefinitionForFunctionException
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition
from pyquibbler.refactor.quib.quib import Quib


@dataclass
class FunctionRunner(ABC):
    func_with_args_values: FuncWithArgsValues
    call_func_with_quibs: bool
    graphics_collections: Optional[np.array]

    @property
    def kwargs(self):
        return self.func_with_args_values.args_values.kwargs

    @property
    def args(self):
        return self.func_with_args_values.args_values.args

    @property
    def func(self):
        return self.func_with_args_values.func

    def _flat_graphics_collections(self):
        return list(self._graphics_collections.flat) if self._graphics_collections else []

    def _get_loop_shape(self):
        return ()

    def _initialize_graphics_collections(self):
        """
        Initialize the array representing all the graphics_collection objects for all iterations of the function
        """
        loop_shape = self._get_loop_shape()
        if self.graphics_collections is not None and self.graphics_collections.shape != loop_shape:
            for graphics_collection in self._flat_graphics_collections():
                graphics_collection.remove_artists()
            self.graphics_collections = None
        if self.graphics_collections is None:
            self.graphics_collections = create_array_from_func(GraphicsCollection, loop_shape)

    # We cache the type, so quibs without cache will still remember their types.
    def get_type(self) -> Type:
        """
        Get the type of wrapped value.
        """
        return type(self._run_on_path(None))

    # We cache the shape, so quibs without cache will still remember their shape.
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        res = self._run_on_path(None)

        try:
            return np.shape(res)
        except ValueError:
            if hasattr(res, '__len__'):
                return len(res),
            raise

    def get_ndim(self) -> int:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        res = self._run_on_path(None)

        try:
            return np.ndim(res)
        except ValueError:
            if hasattr(res, '__len__'):
                return 1
            raise

    @abstractmethod
    def _run_on_path(self, valid_path: Optional[Path]):
        pass

    @property
    def _func_definition(self) -> OverrideDefinition:
        from pyquibbler.refactor.overriding import get_definition_for_function
        return get_definition_for_function(self.func)

    def _get_data_source_quibs(self):
        try:
            return set(iter_objects_of_type_in_object_shallowly(Quib, [
                self.func_with_args_values.args_values[argument]
                for argument in self._func_definition.data_source_arguments
            ]))
        except CannotFindDefinitionForFunctionException:
            return set()

    def _is_quib_a_data_source(self, quib):
        return quib in self._get_data_source_quibs()

    def initialize_and_run_on_path(self, valid_path: Path):
        self._initialize_graphics_collections()
        return self._run_on_path(valid_path)
