from __future__ import annotations

import weakref
from typing import Optional, Type, Tuple, Dict, Callable

from pyquibbler.cache import Cache

from pyquibbler.function_definitions import FuncCall, FuncArgsKwargs
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.path import Path
from pyquibbler.quib.func_calling.exceptions import CannotCalculateShapeException
from pyquibbler.quib.func_calling.result_metadata import ResultMetadata
from pyquibbler.quib.func_calling.utils import create_array_from_func
from pyquibbler.quib.quib import Quib, QuibHandler


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
