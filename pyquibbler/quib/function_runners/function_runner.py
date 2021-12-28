from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from typing import Optional, Type, Tuple, Dict, TYPE_CHECKING

import numpy as np

from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from pyquibbler.quib.function_runners.utils import cache_method_until_full_invalidation
from pyquibbler.quib.graphics.graphics_function_quib import create_array_from_func
from pyquibbler.refactor.graphics.graphics_collection import GraphicsCollection
from pyquibbler.refactor.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.refactor.quib.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.translation.types import Source
from pyquibbler.utils import convert_args_and_kwargs


if TYPE_CHECKING:
    from pyquibbler.refactor.overriding.override_definition import OverrideDefinition


@dataclass
class FunctionRunner(ABC):
    func_with_args_values: FuncWithArgsValues
    call_func_with_quibs: bool
    graphics_collections: Optional[np.array]
    is_known_graphics_func: bool
    method_cache: Dict = field(default_factory=dict)

    @property
    def kwargs(self):
        return self.func_with_args_values.args_values.kwargs

    @property
    def args(self):
        return self.func_with_args_values.args_values.args

    @property
    def func(self):
        return self.func_with_args_values.func

    def flat_graphics_collections(self):
        return list(self.graphics_collections.flat) if self.graphics_collections else []

    def _get_loop_shape(self):
        return ()

    def _initialize_graphics_collections(self):
        """
        Initialize the array representing all the graphics_collection objects for all iterations of the function
        """
        loop_shape = self._get_loop_shape()
        if self.graphics_collections is not None and self.graphics_collections.shape != loop_shape:
            for graphics_collection in self.flat_graphics_collections():
                graphics_collection.remove_artists()
            self.graphics_collections = None
        if self.graphics_collections is None:
            self.graphics_collections = create_array_from_func(GraphicsCollection, loop_shape)

    # We cache the type, so quibs without cache will still remember their types.
    @cache_method_until_full_invalidation
    def get_type(self) -> Type:
        """
        Get the type of wrapped value.
        """
        return type(self.initialize_and_run_on_path(None))

    # We cache the shape, so quibs without cache will still remember their shape.
    @cache_method_until_full_invalidation
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        res = self.initialize_and_run_on_path(None)

        try:
            return np.shape(res)
        except ValueError:
            if hasattr(res, '__len__'):
                return len(res),
            raise

    @cache_method_until_full_invalidation
    def get_ndim(self) -> int:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        res = self.initialize_and_run_on_path(None)

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
        from pyquibbler.refactor.overriding import CannotFindDefinitionForFunctionException
        try:
            return set(iter_objects_of_type_in_object_shallowly(Quib, [
                self.func_with_args_values.args_values[argument]
                for argument in self._func_definition.data_source_arguments
            ]))
        except CannotFindDefinitionForFunctionException:
            return set()

    def get_func_with_args_values_for_translation(self, data_source_quibs_to_paths: Dict[Quib, Path]):
        data_source_quibs = self._get_data_source_quibs()
        data_sources_to_quibs = {}

        def _replace_quib_with_source(_, arg):
            def _replace(q):
                if isinstance(q, Quib):
                    if q in data_source_quibs:
                        source = Source(q.get_value_valid_at_path(data_source_quibs_to_paths.get(q)))
                        data_sources_to_quibs[source] = q
                    else:
                        source = Source(q.get_value_valid_at_path([]))
                    return source
                return q
            return recursively_run_func_on_object(_replace, arg, max_depth=SHALLOW_MAX_DEPTH)

        args, kwargs = convert_args_and_kwargs(_replace_quib_with_source, self.args, self.kwargs)
        return FuncWithArgsValues.from_function_call(
            func=self.func,
            args=args,
            kwargs=kwargs,
            include_defaults=False
        ), data_sources_to_quibs

    def is_quib_a_data_source(self, quib):
        return quib in self._get_data_source_quibs()

    @property
    def _did_create_graphics(self) -> bool:
        return any(graphics_collection.artists for graphics_collection in self.flat_graphics_collections())

    @property
    def func_can_create_graphics(self):
        return self.is_known_graphics_func or self._did_create_graphics

    def initialize_and_run_on_path(self, valid_path: Optional[Path]):
        self._initialize_graphics_collections()
        return self._run_on_path(valid_path)
