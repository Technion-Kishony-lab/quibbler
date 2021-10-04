from typing import Callable, TYPE_CHECKING

from matplotlib.backend_bases import MouseEvent, PickEvent

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib

GRAPHICS_REVERSE_ASSIGNERS = {}


def graphics_reverse_assigner(graphics_func_name_to_handle: str):
    """
    Decorate a function capable of reverse assigning to argument quibs given a mouse event
    """
    def _decorator(func: Callable[[PickEvent, MouseEvent, 'GraphicsFunctionQuib'], None]):
        GRAPHICS_REVERSE_ASSIGNERS[graphics_func_name_to_handle] = func
        return func
    return _decorator


def reverse_graphics_function_quib(graphics_function_quib: 'GraphicsFunctionQuib',
                                   pick_event: PickEvent,
                                   mouse_event: MouseEvent):
    """
    Reverse a graphics function quib, assigning to all it's arguments values based on pick event and mouse event
    """
    reverse_assigner_func = GRAPHICS_REVERSE_ASSIGNERS.get(graphics_function_quib.func.__qualname__)
    if reverse_assigner_func is not None:
        reverse_assigner_func(pick_event=pick_event,
                              mouse_event=mouse_event,
                              function_quib=graphics_function_quib)
