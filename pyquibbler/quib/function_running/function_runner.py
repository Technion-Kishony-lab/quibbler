from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from sys import getsizeof
from time import perf_counter
from typing import Optional, Type, Tuple, Dict, Any, ClassVar, Set, Mapping, Callable

import numpy as np
from matplotlib.widgets import AxesWidget

from pyquibbler.path.path_component import Path
from pyquibbler.cache.cache import Cache
from pyquibbler.cache.holistic_cache import PathCannotHaveComponentsException
from pyquibbler.cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.quib import consts
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.cache.cache_utils import get_uncached_paths_matching_path, \
    _truncate_path_to_match_shallow_caches, _ensure_cache_matches_result, \
    get_cached_data_at_truncated_path_given_result_at_uncached_path
from pyquibbler.quib.function_running.cache_behavior import CacheBehavior
from pyquibbler.quib.function_running.exceptions import CannotCalculateShapeException
from pyquibbler.quib.function_running.result_metadata import ResultMetadata
from pyquibbler.quib.function_running.utils import cache_method_until_full_invalidation, \
    create_array_from_func, proxify_args
from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.quib_guard import QuibGuard
from pyquibbler.quib.utils.func_call_utils import get_args_and_kwargs_valid_at_quibs_to_paths, \
    get_data_source_quibs
from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation
from pyquibbler.translation.exceptions import NoTranslatorsFoundException
from pyquibbler.translation.translate import backwards_translate


@dataclass
class FunctionRunner(ABC):
    DEFAULT_CACHE_BEHAVIOR: ClassVar[CacheBehavior] = CacheBehavior.AUTO

    func_call: FuncCall
    call_func_with_quibs: bool
    graphics_collections: Optional[np.array]
    method_cache: Dict = field(default_factory=dict)
    caching: bool = False
    cache: Optional[Cache] = None
    default_cache_behavior: CacheBehavior = DEFAULT_CACHE_BEHAVIOR
    _result_metadata: Optional[ResultMetadata] = None

    # TODO: is there a better way to do this?
    artists_creation_callback: Callable = None

    def __hash__(self):
        return id(self)

    @classmethod
    def from_(cls, func_call: FuncCall, call_func_with_quibs: bool, *args, **kwargs):
        return cls(func_call=func_call, call_func_with_quibs=call_func_with_quibs, *args, **kwargs)

    @property
    def kwargs(self):
        return self.func_call.args_values.kwargs

    @property
    def args(self):
        return self.func_call.args_values.args

    @property
    def func(self):
        return self.func_call.func

    def flat_graphics_collections(self):
        return list(self.graphics_collections.flat) if self.graphics_collections is not None else []

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
        if self.func_call.get_func_definition().is_random_func or self.func_can_create_graphics:
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

    def _run_shit(self):
        pass

    def _get_representative_value(self):
        return self.get_value_valid_at_path(None)

    def _get_metadata(self):
        if not self._result_metadata:
            result = self.get_value_valid_at_path(None)
            self._result_metadata = ResultMetadata.from_result(result)

        return self._result_metadata

    def get_type(self) -> Type:
        """
        Get the type of wrapped value.
        """
        return self._get_metadata().type

    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        metadata = self._get_metadata()
        if metadata.shape is None:
            raise CannotCalculateShapeException()
        return metadata.shape

    def get_ndim(self) -> int:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        metadata = self._get_metadata()
        if metadata.ndim is None:
            raise CannotCalculateShapeException()
        return metadata.ndim

    @property
    def _did_create_graphics(self) -> bool:
        return any(graphics_collection.artists for graphics_collection in self.flat_graphics_collections())

    @property
    def func_can_create_graphics(self):
        return self.func_call.get_func_definition().is_known_graphics_func or self._did_create_graphics

    def reset_cache(self):
        self.cache = None
        self.caching = True if self.get_cache_behavior() == CacheBehavior.ON else False

    # TODO: Use FuncCall instead of func, args, kwargs
    def _run_single_call(self, func: Callable, graphics_collection: GraphicsCollection,
                         args: Tuple[Any, ...], kwargs: Mapping[str, Any], quibs_allowed_to_access: Set[Quib]):

        # TODO: quib_guard quib guard
        with graphics_collection.track_and_handle_new_graphics(
                kwargs_specified_in_artists_creation=set(self.kwargs.keys())
        ), QuibGuard(quibs_allowed_to_access):
            with external_call_failed_exception_handling():
                res = func(*args, **kwargs)

            # We don't allow returning quibs as results from functions
            from pyquibbler.quib.quib import Quib
            if isinstance(res, Quib):
                res = res.get_value()
            ####

        if self.artists_creation_callback:
            self.artists_creation_callback(set(graphics_collection.artists))

        return res

    def _backwards_translate_path(self, valid_path: Path) -> Dict[Quib, Path]:
        """
        Backwards translate a path- first attempt without shape + type, and then if G-d's good graces fail us and we
        find we are without the ability to do this, try with shape + type
        """
        if not get_data_source_quibs(self.func_call):
            return {}

        func_call, sources_to_quibs = get_func_call_for_translation(self.func_call)

        try:
            sources_to_paths = backwards_translate(
                func_call=func_call,
                path=valid_path,
            )
        except NoTranslatorsFoundException:
            try:
                sources_to_paths = backwards_translate(
                    in_order=False,
                    func_call=func_call,
                    path=valid_path,
                    shape=self.get_shape(),
                    type_=self.get_type(),
                    **self.get_result_metadata()
                )
            except NoTranslatorsFoundException:
                return {}

        return {
            quib: sources_to_paths.get(source, None)
            for source, quib in sources_to_quibs.items()
        }

    def _run_on_path(self, valid_path: Path):
        graphics_collection: GraphicsCollection = self.graphics_collections[()]

        if self.call_func_with_quibs:
            args, kwargs, quibs_allowed_to_access = proxify_args(self.func_call.args, self.func_call.kwargs)
        else:
            quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
            args, kwargs, quibs_allowed_to_access = get_args_and_kwargs_valid_at_quibs_to_paths(self.func_call,
                                                                                                quibs_to_paths)

        return self._run_single_call(
            func=self.func,
            args=args,
            kwargs=kwargs,
            graphics_collection=graphics_collection,
            quibs_allowed_to_access=quibs_allowed_to_access
        )

    def _run_on_uncached_paths_within_path(self, valid_path: Path):
        uncached_paths = get_uncached_paths_matching_path(cache=self.cache, path=valid_path)

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

    def get_result_metadata(self) -> Dict:
        return {}

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
