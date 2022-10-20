from __future__ import annotations

import numpy as np

from dataclasses import dataclass, field

# types:
from typing import Optional, Type, Dict, Callable, Any, List, Union
from pyquibbler.quib.quib import Quib
from pyquibbler.utilities.general_utils import Shape
from pyquibbler.function_definitions import FuncCall

# graphics
from pyquibbler.graphics.graphics_collection import GraphicsCollection

# cache
from pyquibbler.quib.func_calling.cache_mode import CacheMode
from pyquibbler.cache import Cache

# translation
from pyquibbler.path import Path
from pyquibbler.type_translation.run_conditions import TypeTranslateRunCondition
from pyquibbler.type_translation.translate import translate_type
from pyquibbler.utilities.multiple_instance_runner import NoRunnerWorkedException

from .utils import create_array_from_func, get_shape_from_result


@dataclass
class QuibFuncCall(FuncCall):
    """
    Represents a FuncCall with Quibs as argument sources- this will handle running a function with quibs as arguments,
    by caching results and only asking for necessary values from argument quibs
    """

    artists_creation_callback: Optional[Callable] = None
    graphics_collections: Optional[np.ndarray[GraphicsCollection]] = None
    method_cache: Dict[Callable, Any] = field(default_factory=dict)
    cache: Optional[Cache] = None
    _caching: bool = False
    result_type: Optional[Type] = None
    result_shape: Optional[Shape] = None
    cache_mode: CacheMode = None

    SOURCE_OBJECT_TYPE = Quib

    def __hash__(self):
        return id(self)

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

    def get_type(self) -> Type:
        """
        Get the type of result value.
        """
        if self.result_type is None:
            self._calculate_type()
        return self.result_type

    def _get_data_argument_types(self) -> List[Type]:
        """
        Get the type of the data arguments.
        """
        data_argument_values = [self.func_args_kwargs.get_arg_value_by_argument(data_argument)
                                for data_argument in self.func_definition.get_data_arguments(self.func_args_kwargs)]

        return [data_argument_value.get_type() if isinstance(data_argument_value, Quib)
                else type(data_argument_value)
                for data_argument_value in data_argument_values]

    def _calculate_type(self):
        if not isinstance(self.func_definition.result_type_or_type_translators, list):
            # result_type_or_type_translators is the pre-determined type
            self.result_type = self.func_definition.result_type_or_type_translators
        else:
            # result_type_or_type_translators is a list of get_type runners
            try:
                # try getting the type of the result without the type of the arguments:
                self.result_type = translate_type(run_condition=TypeTranslateRunCondition.NO_ARGUMENTS_TYPES,
                                                  func_definition=self.func_definition)
            except NoRunnerWorkedException:
                try:
                    # try getting the type of the result based on the type of the arguments:
                    self.result_type = translate_type(run_condition=TypeTranslateRunCondition.WITH_ARGUMENTS_TYPES,
                                                      func_definition=self.func_definition,
                                                      data_arguments_types=self._get_data_argument_types())
                except NoRunnerWorkedException:
                    # we must call teh function to update the type:
                    self.run([None])

    def get_shape(self) -> Shape:
        """
        Get the shape of the result value.
        """
        if self.result_shape is None:
            self._calculate_shape()
        return self.result_shape

    def _calculate_shape(self):
        self.run([None])  # this will update the shape

    def get_ndim(self) -> int:
        """
        Get the number of dimensions of the result value.
        """
        return len(self.get_shape())

    def _update_shape_and_type_from_result(self, result):
        self.result_type = type(result)
        self.result_shape = get_shape_from_result(result)

    @property
    def created_graphics(self) -> bool:
        return any(graphics_collection.artists for graphics_collection in self.flat_graphics_collections())

    @property
    def func_can_create_graphics(self):
        is_graphics = self.func_definition.is_graphics
        return is_graphics or (is_graphics is None and self.created_graphics)

    def on_type_change(self):
        self.method_cache.clear()
        self.result_type = None
        self.result_shape = None

    def invalidate_cache_at_path(self, path: Path):
        pass

    def get_result_metadata(self) -> Dict:
        return {}

    def _run(self) -> Any:
        pass

    def run(self, valid_paths: List[Union[None, Path]]) -> Any:
        result = self._run()
        self._update_shape_and_type_from_result(result)
        return result


class WholeValueNonGraphicQuibFuncCall(QuibFuncCall):

    @property
    def created_graphics(self) -> bool:
        return False

    @property
    def func_can_create_graphics(self):
        return False
