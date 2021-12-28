from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from sys import getsizeof
from time import perf_counter
from typing import Optional, Type, Tuple, Dict, TYPE_CHECKING, Any, ClassVar

import numpy as np
from pyquibbler.quib.assignment import Path
from pyquibbler.refactor.quib.cache_behavior import CacheBehavior
from pyquibbler.quib.function_quibs.cache.cache import Cache
from pyquibbler.quib.function_quibs.cache.holistic_cache import PathCannotHaveComponentsException
from pyquibbler.quib.function_quibs.cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from pyquibbler.quib.function_quibs.utils import FuncWithArgsValues
from pyquibbler.refactor.quib import consts
from pyquibbler.refactor.quib.function_call import _get_uncached_paths_matching_path, \
    _truncate_path_to_match_shallow_caches, _ensure_cache_matches_result, \
    get_cached_data_at_truncated_path_given_result_at_uncached_path
from pyquibbler.refactor.quib.function_runners.utils import cache_method_until_full_invalidation
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

    DEFAULT_CACHE_BEHAVIOR: ClassVar[CacheBehavior] = CacheBehavior.AUTO

    func_with_args_values: FuncWithArgsValues
    call_func_with_quibs: bool
    graphics_collections: Optional[np.array]
    is_known_graphics_func: bool
    is_random_func: bool
    method_cache: Dict = field(default_factory=dict)
    caching: bool = False
    cache: Optional[Cache] = None
    default_cache_behavior: CacheBehavior = DEFAULT_CACHE_BEHAVIOR

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

    def get_cache_behavior(self):
        if self.is_random_func or self.func_can_create_graphics:
            return CacheBehavior.ON
        return self.default_cache_behavior

    def _should_cache(self, result: Any, elapsed_seconds: float):
        """
        Decide if the result of the calculation is worth caching according to its size and the calculation time.
        Note that there is no accurate way (and no efficient way to even approximate) the complete size of composite
        types in python, so we only measure the outer size of the object.
        """
        cache_behavior = self.get_cache_behavior()
        if cache_behavior is CacheBehavior.ON:
            return True
        if cache_behavior is CacheBehavior.OFF:
            return False
        assert cache_behavior is CacheBehavior.AUTO, \
            f'self.cache_behavior has unexpected value: "{cache_behavior}"'
        return elapsed_seconds > consts.MIN_SECONDS_FOR_CACHE \
            and getsizeof(result) / elapsed_seconds < consts.MAX_BYTES_PER_SECOND

    def _run_on_uncached_paths_within_path(self, valid_path: Path):
        uncached_paths = _get_uncached_paths_matching_path(cache=self.cache, path=valid_path)

        if len(uncached_paths) == 0:
            return self.cache.get_value()

        result = None

        for uncached_path in uncached_paths:
            result = self._run_on_path(uncached_path)

            truncated_path = _truncate_path_to_match_shallow_caches(uncached_path)
            self.cache = _ensure_cache_matches_result(self.cache, result)

            if truncated_path is not None:
                self.cache = transform_cache_to_nd_if_necessary_given_path(self.cache, truncated_path)
                value = get_cached_data_at_truncated_path_given_result_at_uncached_path(self.cache,
                                                                                        result,
                                                                                        truncated_path,
                                                                                        uncached_path)

                try:
                    self.cache.set_valid_value_at_path(truncated_path, value)
                except PathCannotHaveComponentsException:
                    # We do not have a diverged cache for this type, we can't store the value; this is not a problem as
                    # everything will work as expected, but we will simply not cache
                    assert len(uncached_paths) == 1, "There should never be a situation in which we have multiple " \
                                                     "uncached paths but our cache can't handle setting a value at a " \
                                                     "specific component"
                else:
                    # We need to get the result from the cache (as opposed to simply using the last run), since we
                    # don't want to only take the last run
                    result = self.cache.get_value()

                    # sanity
                    assert len(self.cache.get_uncached_paths(truncated_path)) == 0

        return result

    def _get_representative_value(self):
        return self.get_value_valid_at_path(None)

    # We cache the type, so quibs without cache will still remember their types.
    @cache_method_until_full_invalidation
    def get_type(self) -> Type:
        """
        Get the type of wrapped value.
        """
        return type(self._get_representative_value())

    # We cache the shape, so quibs without cache will still remember their shape.
    @cache_method_until_full_invalidation
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        res = self._get_representative_value()

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
        res = self._get_representative_value()

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

    def reset_cache(self):
        self.cache = None
        self.caching = True if self.get_cache_behavior() == CacheBehavior.ON else False

    def get_value_valid_at_path(self, path: Optional[Path]) -> Any:
        """
        Get the actual data that this quib represents, valid at the path given in the argument.
        The value will necessarily return in the shape of the actual result, but only the values at the given path
        are guaranteed to be valid
        """
        self._initialize_graphics_collections()
        start_time = perf_counter()

        result = self._run_on_uncached_paths_within_path(path)

        elapsed_seconds = perf_counter() - start_time

        if self._should_cache(result, elapsed_seconds):
            self.caching = True
        if not self.caching:
            self.cache = None

        return result
