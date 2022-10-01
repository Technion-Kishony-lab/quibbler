
def recursively_replace_objects_with_index_codes(obj: Any, focal_source: Source,
                                                 path_in_source: Path = missing
                                                 ) -> Union[IndexCode, NDArray[IndexCode]]:
    """
    Recursively convert obj array-like elements to np.int64 "index codes", indicating the linear indexing of
    the focal_source, or specifying other elements according to IndexCode.
    When path_in_source is given, within source elements that are not within the path are labeled as NON_CHOSEN_ELEMENT.
    """
    is_focal_source = obj is focal_source
    is_source = isinstance(obj, Source)
    if is_source:
        obj = obj.value

    if is_focal_source:
        if is_scalar_np(obj):
            return IndexCode.FOCAL_SOURCE_SCALAR
        array_of_linear_indices = np.arange(np.size(obj)).reshape(np.shape(obj))
        if path_in_source is missing:
            source_array = array_of_linear_indices
        else:
            source_array = np.full(np.shape(obj), IndexCode.NON_CHOSEN_ELEMENT)
            deep_assign_data_in_path(source_array, path_in_source,
                                     deep_get(array_of_linear_indices, path_in_source))
        source_array = de_array_by_template(source_array, obj)
        return source_array

    if is_scalar_np(obj):
        return IndexCode.OTHERS_ELEMENT

    if isinstance(obj, np.ndarray):
        return np.full(np.shape(obj), IndexCode.OTHERS_ELEMENT)

    converted_sub_args = []
    source_index = None if path_to_source is missing else path_to_source[0].component
    for sub_arg_index, sub_arg in enumerate(arg):
        if source_index != sub_arg_index:
            converted_sub_arg, _ = \
                convert_arg_and_source_to_array_of_indices(sub_arg, missing, missing, path_in_source)
        else:
            converted_sub_arg, new_path_to_source = \
                convert_arg_and_source_to_array_of_indices(sub_arg, focal_source, path_to_source[1:], path_in_source)
        converted_sub_args.append(converted_sub_arg)

    shared_shape = get_shared_shape(converted_sub_args)

    if path_to_source is not missing:
        path_to_source = path_to_source[len(path_to_source) - len(new_path_to_source)
                                        - (len(shared_shape) - len(converted_sub_args[source_index].shape)):]
    for sub_arg_index, converted_sub_arg in enumerate(converted_sub_args):
        if converted_sub_arg.shape != shared_shape:
            converted_sub_args[sub_arg_index] = \
                np.full(shared_shape, _non_focal_source_scalar(np.any(converted_sub_arg > MAXIMAL_NON_FOCAL_SOURCE)))

    return np.array(converted_sub_args), path_to_source




def convert_arg_and_source_to_array_of_indices(arg: Any,
                                               focal_source: Source,
                                               path_to_source: Path,
                                               path_in_source: Any = missing) -> Tuple[np.ndarray, Path]:
    """
    Convert arg to an array of int64 with values matching the linear indexing of focal_source,
    or specifying other elements according to IndexCode.
    """
    is_focal_source = arg is focal_source
    is_source = isinstance(arg, Source)
    if is_source:
        arg = arg.value

    if is_focal_source:
        if is_scalar_np(arg):
            return IndexCode.FOCAL_SOURCE_SCALAR, path_to_source
        if path_in_source is missing:
            return np.arange(np.size(arg)).reshape(np.shape(arg)), path_to_source
        else:
            val = np.full(np.shape(arg), IndexCode.NON_CHOSEN_ELEMENT)
            val[path_in_source] = IndexCode.CHOSEN_ELEMENT
            return val, path_to_source

    if is_scalar_np(arg):
        return _non_focal_source_scalar(focal_source is not missing), path_to_source

    if isinstance(arg, np.ndarray):
        return np.full(np.shape(arg), IndexCode.OTHERS_ELEMENT), path_to_source

    converted_sub_args = []
    source_index = None if path_to_source is missing else path_to_source[0].component
    for sub_arg_index, sub_arg in enumerate(arg):
        if source_index != sub_arg_index:
            converted_sub_arg, _ = \
                convert_arg_and_source_to_array_of_indices(sub_arg, missing, missing, path_in_source)
        else:
            converted_sub_arg, new_path_to_source = \
                convert_arg_and_source_to_array_of_indices(sub_arg, focal_source, path_to_source[1:], path_in_source)
        converted_sub_args.append(converted_sub_arg)

    shared_shape = get_shared_shape(converted_sub_args)

    if path_to_source is not missing:
        path_to_source = path_to_source[len(path_to_source) - len(new_path_to_source)
                                        - (len(shared_shape) - len(converted_sub_args[source_index].shape)):]
    for sub_arg_index, converted_sub_arg in enumerate(converted_sub_args):
        if converted_sub_arg.shape != shared_shape:
            converted_sub_args[sub_arg_index] = \
                np.full(shared_shape, _non_focal_source_scalar(np.any(converted_sub_arg > MAXIMAL_NON_FOCAL_SOURCE)))

    return np.array(converted_sub_args), path_to_source


# strategy:
# When a numpy transposition function (e.g. array, transpose, etc) is applied on an object,
# it first creates an array of this object. If the object contains quibs, we need to determine where these quibs
# fit within the created array. Our strategy is to deeply/recursively replace the object with same-type and same-shape
# object with any scalars (non array-like, namely not array, list, or tuple), replaced with scalar np.64 values
# representing IndexCode.

def recursively_replace_objects_with_index_codes(obj: Any, focal_source: Source,
                                                 path_in_source: Path = missing
                                                 ) -> Union[IndexCode, NDArray[IndexCode]]:
    """
    Recursively convert obj array-like elements to np.int64 "index codes", indicating the linear indexing of
    the focal_source, or specifying other elements according to IndexCode.
    When path_in_source is given, within source elements that are not within the path are labeled as NON_CHOSEN_ELEMENT.
    """
    is_focal_source = obj is focal_source
    if isinstance(obj, Source):
        obj = obj.value

    if is_focal_source:
        if is_scalar_np(obj):
            return IndexCode.FOCAL_SOURCE_SCALAR
        array_of_linear_indices = np.arange(np.size(obj)).reshape(np.shape(obj))
        if path_in_source is missing:
            return array_of_linear_indices
        else:
            source_array = np.full(np.shape(obj), IndexCode.NON_CHOSEN_ELEMENT)
            deep_assign_data_in_path(source_array, path_in_source,
                                     deep_get(array_of_linear_indices, path_in_source))
            return source_array

    if is_scalar_np(obj):
        return IndexCode.OTHERS_ELEMENT

    if isinstance(obj, np.ndarray):
        return np.full(np.shape(obj), IndexCode.OTHERS_ELEMENT)

    converted_sub_args = []
    source_index = None if path_to_source is missing else path_to_source[0].component
    for sub_arg_index, sub_arg in enumerate(arg):
        if source_index != sub_arg_index:
            converted_sub_arg, _ = \
                convert_arg_and_source_to_array_of_indices(sub_arg, missing, missing, path_in_source)
        else:
            converted_sub_arg, new_path_to_source = \
                convert_arg_and_source_to_array_of_indices(sub_arg, focal_source, path_to_source[1:], path_in_source)
        converted_sub_args.append(converted_sub_arg)

    shared_shape = get_shared_shape(converted_sub_args)

    if path_to_source is not missing:
        path_to_source = path_to_source[len(path_to_source) - len(new_path_to_source)
                                        - (len(shared_shape) - len(converted_sub_args[source_index].shape)):]
    for sub_arg_index, converted_sub_arg in enumerate(converted_sub_args):
        if converted_sub_arg.shape != shared_shape:
            converted_sub_args[sub_arg_index] = \
                np.full(shared_shape, _non_focal_source_scalar(np.any(converted_sub_arg > MAXIMAL_NON_FOCAL_SOURCE)))

    return np.array(converted_sub_args), path_to_source
