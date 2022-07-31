def _get_argument_used_in_current_func_call_for_argument(self, argument: Argument):
    """
    Get the argument actually used in this specific funccall corresponding to the given parameter `argument`.

    For example, given:

    def my_func(a):
        pass

    `a` could be referenced by both PositionalArgument(0) or KeywordArgument("a")

    Given either of the arguments PositionalArgument(0) or KeywordArgument("a"), this func will return the one
    actually being used in this instance
    """
    try:
        create_source_location(argument=argument, path=[]).find_in_args_kwargs(self.args, self.kwargs)
        return argument
    except (KeyError, IndexError):
        return self.func_definition.get_corresponding_argument(argument)


def _get_locations_within_arguments_and_values(self, arguments_and_values):
    return [
        create_source_location(self._get_argument_used_in_current_func_call_for_argument(argument), path)
        for argument, value in arguments_and_values
        for path in get_paths_for_objects_of_type(obj=value, type_=self.SOURCE_OBJECT_TYPE)
    ]

