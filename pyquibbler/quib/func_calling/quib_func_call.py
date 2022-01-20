from __future__ import annotations

from sys import getsizeof
from time import perf_counter
from typing import Optional, Type, Tuple, Dict, Any, ClassVar, Set, Mapping, Callable, List

from pyquibbler.cache.cache_utils import get_uncached_paths_matching_path, \
    _truncate_path_to_match_shallow_caches, _ensure_cache_matches_result, \
    get_cached_data_at_truncated_path_given_result_at_uncached_path
from pyquibbler.cache.holistic_cache import PathCannotHaveComponentsException
from pyquibbler.cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from pyquibbler.function_definitions import FuncCall, PositionalSourceLocation, SourceLocation, KeywordSourceLocation, \
    load_source_locations_before_running, ArgsValues
from pyquibbler.function_definitions.types import PositionalArgument, KeywordArgument
from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.path.path_component import Path
from pyquibbler.quib import consts
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.func_calling.cache_behavior import CacheBehavior
from pyquibbler.quib.func_calling.exceptions import CannotCalculateShapeException
from pyquibbler.quib.func_calling.result_metadata import ResultMetadata
from pyquibbler.quib.func_calling.utils import create_array_from_func
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.quib_guard import QuibGuard
from pyquibbler.quib.quib_ref import QuibRef
from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation
from pyquibbler.translation.exceptions import NoTranslatorsFoundException
from pyquibbler.translation.translate import backwards_translate
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type


class QuibFuncCall(FuncCall):
    """
    Represents a FuncCall with Quibs as argument sources- this will handle running a function with quibs as arguments,
    by caching results and only asking for necessary values from argument quibs
    """

    SOURCE_OBJECT_TYPE = Quib
    DEFAULT_CACHE_BEHAVIOR = CacheBehavior.AUTO

    def __init__(self, func: Callable, args_values: ArgsValues, default_cache_behavior: CacheBehavior,
                 call_func_with_quibs: bool, artists_creation_callback: Callable = None):
        super(QuibFuncCall, self).__init__(func=func, args_values=args_values)
        self.graphics_collections = None
        self.method_cache = {}
        self.cache = None
        self.default_cache_behavior = default_cache_behavior
        self.artists_creation_callback = artists_creation_callback
        self._caching = False
        self._call_func_with_quibs = call_func_with_quibs
        self._result_metadata = None
        self._quib_ref_locations: Optional[List[SourceLocation]] = None

    def flat_graphics_collections(self):
        return list(self.graphics_collections.flat) if self.graphics_collections is not None else []

    def _get_loop_shape(self):
        """
        Get the shape in which the function will loop (ie shape of iterations of the function)
        """
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
        if self.get_func_definition().is_random_func or self.func_can_create_graphics:
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

    def _get_representative_value(self):
        return self.run(valid_path=None)

    def _get_metadata(self):
        if not self._result_metadata:
            result = self.run(valid_path=None)
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
        return self.get_func_definition().is_known_graphics_func or self._did_create_graphics

    def reset_cache(self):
        self.cache = None
        self._caching = True if self.get_cache_behavior() == CacheBehavior.ON else False
        self._result_metadata = None

    def on_type_change(self):
        self.method_cache.clear()

    def _run_single_call(self, func: Callable, graphics_collection: GraphicsCollection,
                         args: Tuple[Any, ...], kwargs: Mapping[str, Any], quibs_allowed_to_access: Set[Quib]):
        with graphics_collection.track_and_handle_new_graphics(
                kwargs_specified_in_artists_creation=set(self.kwargs.keys())
        ), QuibGuard(quibs_allowed_to_access):
            with external_call_failed_exception_handling():
                res = func(*args, **kwargs)

            # We don't allow returning quibs as results from functions
            from pyquibbler.quib.quib import Quib
            if isinstance(res, Quib):
                res = res.get_value()

        if self.artists_creation_callback:
            self.artists_creation_callback(set(graphics_collection.artists))

        return res

    def _backwards_translate_path(self, valid_path: Path) -> Dict[Quib, Path]:
        """
        Backwards translate a path- first attempt without shape + type, and then if G-d's good graces fail us and we
        find we are without the ability to do this, try with shape + type
        """
        if not self.get_data_sources():
            return {}

        func_call, sources_to_quibs = get_func_call_for_translation(self)

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

    def _proxify_args(self):
        from pyquibbler.quib.specialized_functions.proxy import create_proxy
        quibs_allowed_to_access = set()

        def _proxify(arg):
            proxy = create_proxy(arg)
            quibs_allowed_to_access.add(proxy)
            return proxy

        args, kwargs = self.transform_sources_in_args_kwargs(transform_parameter_func=_proxify,
                                                             transform_data_source_func=_proxify)
        return args, kwargs, quibs_allowed_to_access

    def _run_on_path(self, valid_path: Path):
        graphics_collection: GraphicsCollection = self.graphics_collections[()]

        if self._call_func_with_quibs:
            args, kwargs, quibs_allowed_to_access = self._proxify_args()
        else:
            quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
            args, kwargs, quibs_allowed_to_access = self.get_args_and_kwargs_valid_at_quibs_to_paths(quibs_to_paths)

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

    def _load_source_locations(self):
        super(QuibFuncCall, self)._load_source_locations()
        if self._quib_ref_locations is None:
            self._quib_ref_locations: List[SourceLocation] = [
                PositionalSourceLocation(PositionalArgument(i), path)
                for i, arg in enumerate(self.args)
                for path in get_paths_for_objects_of_type(arg, type_=QuibRef)
            ]
            self._quib_ref_locations.extend([
                KeywordSourceLocation(KeywordArgument(key), path)
                for key, value in self.kwargs.items()
                for path in get_paths_for_objects_of_type(value, type_=QuibRef)
            ])

    @load_source_locations_before_running
    def get_args_and_kwargs_valid_at_quibs_to_paths(self,
                                                    quibs_to_valid_paths: Dict[Quib, Optional[Path]]):
        """
        Prepare arguments to call self.func with - replace quibs with values valid at the given path,
        and QuibRefs with quibs.
        """

        quibs_allowed_to_access = set()

        def _transform_data_source_quib(quib):
            # If the quib is a data source, and we didn't see it in the result, we don't need it to be valid at any
            # paths (it did not appear in quibs_to_paths)
            path = quibs_to_valid_paths.get(quib)
            return quib.get_value_valid_at_path(path)

        def _transform_parameter_source_quib(quib):
            # This is a paramater quib- we always need a parameter quib to be completely valid regardless of where
            # we need ourselves (this quib) to be valid
            return quib.get_value_valid_at_path([])

        new_args, new_kwargs = self.transform_sources_in_args_kwargs(
            transform_data_source_func=_transform_data_source_quib,
            transform_parameter_func=_transform_parameter_source_quib
        )

        for location in self._quib_ref_locations:
            quib_ref = location.find_in_args_kwargs(args=new_args, kwargs=new_kwargs)
            quibs_allowed_to_access.add(quib_ref.quib)
            new_args, new_kwargs = location.set_in_args_kwargs(args=new_args, kwargs=new_kwargs, value=quib_ref.quib)

        return new_args, new_kwargs, quibs_allowed_to_access

    def get_result_metadata(self) -> Dict:
        return {}

    def run(self, valid_path: Optional[Path]) -> Any:
        """
        Get the actual data that this quib represents, valid at the path given in the argument.
        The value will necessarily return in the shape of the actual result, but only the values at the given path
        are guaranteed to be valid
        """
        self._initialize_graphics_collections()

        start_time = perf_counter()

        result = self._run_on_uncached_paths_within_path(valid_path)

        elapsed_seconds = perf_counter() - start_time

        if self._should_cache(result, elapsed_seconds):
            self._caching = True
        if not self._caching:
            self.cache = None

        return result
