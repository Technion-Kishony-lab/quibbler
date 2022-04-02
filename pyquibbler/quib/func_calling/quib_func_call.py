from __future__ import annotations

import weakref
from contextlib import ExitStack
from sys import getsizeof
from time import perf_counter
from typing import Optional, Type, Tuple, Dict, Any, Set, Mapping, Callable, List, Union

from pyquibbler.cache.cache_utils import _truncate_path_to_match_shallow_caches, _ensure_cache_matches_result, \
    get_cached_data_at_truncated_path_given_result_at_uncached_path
from pyquibbler.cache import PathCannotHaveComponentsException, get_uncached_paths_matching_path, Cache

from pyquibbler.function_definitions import FuncCall, load_source_locations_before_running, FuncArgsKwargs
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.path import Path
from pyquibbler.quib import consts
from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling
from pyquibbler.quib.func_calling.cache_mode import CacheMode
from pyquibbler.quib.func_calling.exceptions import CannotCalculateShapeException
from pyquibbler.quib.func_calling.result_metadata import ResultMetadata
from pyquibbler.quib.func_calling.utils import create_array_from_func
from pyquibbler.quib.quib import Quib, QuibHandler
from pyquibbler.quib.quib_guard import QuibGuard
from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation_with_sources_metadata, \
    get_func_call_for_translation_without_sources_metadata
from pyquibbler.translation import NoTranslatorsFoundException
from pyquibbler.translation.translate import backwards_translate


class QuibFuncCall(FuncCall):
    """
    Represents a FuncCall with Quibs as argument sources- this will handle running a function with quibs as arguments,
    by caching results and only asking for necessary values from argument quibs
    """

    SOURCE_OBJECT_TYPE = Quib

    def __init__(self, artists_creation_callback: Callable = None,
                 quib_handler: QuibHandler = None):
        super(QuibFuncCall, self).__init__()
        self.graphics_collections = None
        self.method_cache = {}
        self.cache: Optional[Cache] = None
        self.quib_handler_ref = weakref.ref(quib_handler)
        self.artists_creation_callback = artists_creation_callback
        self._caching = False
        self._result_metadata = None

    @property
    def quib_handler(self) -> QuibHandler:
        return self.quib_handler_ref()

    @property
    def func_args_kwargs(self) -> FuncArgsKwargs:
        return self.quib_handler.func_args_kwargs

    @property
    def func_definition(self) -> FuncDefinition:
        return self.quib_handler.func_definition

    @property
    def _pass_quibs(self):
        return self.func_definition.pass_quibs

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

    def _get_metadata(self):
        if not self._result_metadata:
            result = self.run([None])
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
    def created_graphics(self) -> bool:
        return any(graphics_collection.artists for graphics_collection in self.flat_graphics_collections())

    @property
    def func_can_create_graphics(self):
        is_graphics = self.func_definition.is_graphics
        return is_graphics or (is_graphics is None and self.created_graphics)

    def on_type_change(self):
        self.method_cache.clear()

    def invalidate_cache_at_path(self, path: Path):
        pass

    def get_result_metadata(self) -> Dict:
        return {}
