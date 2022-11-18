from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition


FUNC_DEFINITION_GRAPHICS = create_or_reuse_func_definition(
    is_graphics=True,
)

FUNC_DEFINITION_GRAPHICS_AXES_SETTER = create_or_reuse_func_definition(
    is_graphics=True,
    is_artist_setter=True,
)
