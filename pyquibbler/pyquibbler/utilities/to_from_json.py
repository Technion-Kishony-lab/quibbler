import ast


def to_json_compatible(obj):
    """
    Recursively converts Python objects into a JSON‑serializable format.
    """
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {repr(k): to_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_compatible(item) for item in obj]
    else:
        return repr(obj)


def from_json_compatible(obj):
    """
    Converts a JSON compatible object back to its original Python type.
    """
    if isinstance(obj, dict):
        return {ast.literal_eval(k): from_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [from_json_compatible(item) for item in obj]
    elif isinstance(obj, str):
        return ast.literal_eval(obj)
    else:
        return obj


def test_to_from_json_compatible():
    """
    Test the to_json_compatible and from_json_compatible functions.
    """
    original = {
        'key1': 123,
        'key2': [1, 2, 3],
        'key3': {'nested_key': 456},
        'key4': None,
        'key5': True,
        'key6': False,
        'key7': 3.14,
    }

    json_compatible = to_json_compatible(original)
    assert isinstance(json_compatible, dict)

    restored = from_json_compatible(json_compatible)
    assert original == restored
