import pytest

from pyquibbler.quib.save_assignments import FileNotDefinedException, ResponseToFileNotDefined


def test_quib_wont_save_without_assigned_name(create_quib_with_return_value):
    example_quib = create_quib_with_return_value(5, allow_overriding=True)
    example_quib.assign(10)

    with pytest.raises(FileNotDefinedException):
        example_quib.save(ResponseToFileNotDefined.RAISE)
