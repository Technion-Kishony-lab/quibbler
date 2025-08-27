from dataclasses import dataclass

import numpy as np
from pytest import fixture

from pyquibbler import iquib, quiby, is_quiby, not_quiby
from pyquibbler.quib.graphics.event_handling.utils import is_quib
from pyquibbler.utilities.basic_types import Mutable


def normal_func_that_cannot_work_directly_on_quibs(x, y, z):
    assert not is_quib(x)
    assert not is_quib(y)
    assert not is_quib(z)
    return x + y + z


@fixture
def dummy_graphics_quib():
    return Mutable(None)


@fixture
def x_value():
    return np.array([1, 2])


@fixture
def y_value():
    return 10


@fixture
def z_value():
    return 100


@fixture
def x_quib(x_value):
    return iquib(x_value)


@fixture
def y_quib(y_value):
    return iquib(y_value)


@fixture()
def quiby_class(dummy_graphics_quib):

    @quiby(create_quib=None)
    class Obj:
        CALLED = {'quiby_property': 0, 'quiby_method': 0, 'dependent_quiby_method': 0,
                  'set_x_value_at_idx': 0, 'create_graphics': 0}

        def __init__(self, x, y, z):
            self.x = x  # quib
            self.y = y  # quib
            self.z = z  # not a quib
            dummy_graphics_quib.set(None)


        @property
        def quiby_property(self):
            self.CALLED['quiby_property'] += 1
            return normal_func_that_cannot_work_directly_on_quibs(self.x, self.y, self.z)

        def quiby_method(self):
            self.CALLED['quiby_method'] += 1
            return normal_func_that_cannot_work_directly_on_quibs(self.x, self.y, self.z)

        def dependent_quiby_method(self, factor):
            self.CALLED['dependent_quiby_method'] += 1
            return self.quiby_method() * factor

        @not_quiby
        def set_x_value_at_idx(self, idx, value):
            self.CALLED['set_x_value_at_idx'] += 1
            self.x[idx] = value

        @quiby(pass_quibs=True, is_graphics=True)
        def create_graphics(self):
            self.CALLED['create_graphics'] += 1
            dummy_graphics_quib.set(self.x + self.y)

        @not_quiby
        def get_bare_x(self):
            # return the quib itself
            return self.x

    return Obj


@fixture
def quiby_obj(quiby_class, x_quib, y_quib, z_value):
    return quiby_class(x_quib, y_quib, z_value)


def test_quiby_class_init(quiby_obj, x_quib, y_quib, z_value):
    assert quiby_obj.x is x_quib
    assert quiby_obj.y is y_quib
    assert quiby_obj.z == z_value
    # assert no function calls were made yet:
    assert all(v == 0 for v in quiby_obj.CALLED.values())


def test_quiby_class_quiby_method(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    quiby_obj.quiby_method()
    assert is_quiby(quiby_obj.quiby_method)
    result = quiby_obj.quiby_method()
    assert is_quib(result)
    assert np.array_equal(result.get_value(), x_value + y_value + z_value)
    x_quib[0] = 20
    assert np.array_equal(result.get_value(), x_value + y_value + z_value + [19, 0])


def test_quiby_class_quiby_property(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    result = quiby_obj.quiby_property
    assert is_quib(result)
    assert np.array_equal(result.get_value(), x_value + y_value + z_value)
    x_quib[0] = 20
    assert np.array_equal(result.get_value(), x_value + y_value + z_value + [19, 0])
    y_quib.assign(50)
    assert np.array_equal(result.get_value(), x_value + 50 + z_value + [19, 0])


def test_quiby_class_dependent_quiby_method(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    result = quiby_obj.dependent_quiby_method(2)
    assert is_quib(result)
    assert np.array_equal(result.get_value(), 2 * (x_value + y_value + z_value))
    x_quib[0] = 20
    assert np.array_equal(result.get_value(), 2 * (x_value + y_value + z_value + [19, 0]))
    y_quib.assign(50)
    assert np.array_equal(result.get_value(), 2 * (x_value + 50 + z_value + [19, 0]))


def test_quiby_class_set_x_value_at_idx(quiby_obj, x_quib, y_quib, x_value, y_value, z_value):
    assert np.array_equal(x_quib.get_value(), [1, 2])  # sanity check
    quiby_obj.set_x_value_at_idx(0, 30)
    assert np.array_equal(x_quib.get_value(), [30, 2])
    result = quiby_obj.quiby_method()
    assert is_quib(result)
    assert np.array_equal(result.get_value(), np.array([30, 2]) + y_value + z_value)
    x_quib[0] = 40
    assert np.array_equal(result.get_value(), np.array([40, 2]) + y_value + z_value)

def test_quiby_class_get_bare_x(quiby_obj, x_quib):
    bare_x = quiby_obj.get_bare_x()
    assert bare_x is x_quib


def test_quiby_class_create_graphics(quiby_obj, x_quib, y_quib, dummy_graphics_quib):
    assert dummy_graphics_quib.val is None
    graphics_quib = quiby_obj.create_graphics()
    assert is_quib(graphics_quib)
    assert np.array_equal(dummy_graphics_quib.val.get_value(), np.array([1, 2]) + 10)
    x_quib[0] = 20
    assert np.array_equal(dummy_graphics_quib.val.get_value(), np.array([20, 2]) + 10)


def test_dataclass_fields():
    @quiby
    @dataclass
    class DataClassObj:
        x: int
        y: int

        def sum(self):
            return self.x + self.y

    obj = DataClassObj(10, 20)
    assert not is_quiby(obj.sum())

    obj.x = iquib(30)
    assert obj.x.get_value() == 30
    result = obj.sum()
    assert is_quib(result)
    assert result.get_value() == 50


def test_dataclass_inheritance():
    @quiby
    @dataclass
    class BaseClass:
        x: int
        
        def base_method(self):
            return self.x * 2

    @quiby
    @dataclass  
    class SubClass(BaseClass):
        y: int
        
        def sub_method(self):
            return self.x + self.y
            
        def combined_method(self):
            return self.base_method() + self.sub_method()

    obj = SubClass(10, 20)

    assert is_quiby(obj.base_method)
    assert is_quiby(obj.sub_method)
    assert is_quiby(obj.combined_method)
    
    # Test with non-quib values
    assert not is_quib(obj.base_method())
    assert not is_quib(obj.sub_method())
    assert not is_quib(obj.combined_method())
    
    # Make x a quib
    obj.x = iquib(30)
    
    # Both base and sub methods should be quiby when x is a quib
    base_result = obj.base_method()
    assert is_quib(base_result)
    assert base_result.get_value() == 60
    
    sub_result = obj.sub_method()
    assert is_quib(sub_result)
    assert sub_result.get_value() == 50
    
    combined_result = obj.combined_method()
    assert is_quib(combined_result)
    assert combined_result.get_value() == 110
    
    # Make y a quib too
    obj.y = iquib(40)
    
    # Verify all methods still work with both quibs
    assert obj.base_method().get_value() == 60  # only depends on x
    assert obj.sub_method().get_value() == 70   # x + y = 30 + 40
    assert obj.combined_method().get_value() == 130  # 60 + 70


def test_dataclass_multiple_inheritance_with_post_init():
    @quiby
    @dataclass
    class Super1:
        x: int
        
        def __post_init__(self):
            self._super1_init_called = True
            
        def super1_method(self):
            return self.x * 3

    @quiby
    @dataclass
    class Super2:
        y: int
        
        def __post_init__(self):
            self._super2_init_called = True
            
        def super2_method(self):
            return self.y * 5

    @quiby
    @dataclass
    class Sub(Super1, Super2):
        z: int
        _super1_init_called: bool = False
        _super2_init_called: bool = False
        _sub_init_called: bool = False
        
        def __post_init__(self):
            Super1.__post_init__(self)
            Super2.__post_init__(self)
            self._sub_init_called = True
            
        def sub_method(self):
            return self.super1_method() + self.super2_method() + self.z
    
    obj = Sub(10, 20, 30)
    
    # Check that all __post_init__ methods were called
    assert obj._super1_init_called
    assert obj._super2_init_called  
    assert obj._sub_init_called
    
    # Check that all methods are quiby
    assert is_quiby(obj.super1_method)
    assert is_quiby(obj.super2_method)
    assert is_quiby(obj.sub_method)
    
    # Test with non-quib values
    assert not is_quib(obj.super1_method())
    assert not is_quib(obj.super2_method())
    assert not is_quib(obj.sub_method())
    
    # Make x a quib
    obj.x = iquib(15)
    
    # Methods depending on x should become quiby
    super1_result = obj.super1_method()
    assert is_quib(super1_result)
    assert super1_result.get_value() == 45  # 15 * 3
    
    sub_result = obj.sub_method()
    assert is_quib(sub_result)
    # x=15, y=10, z=30 -> super1=15*3=45, super2=10*5=50, total=45+50+30=125
    assert sub_result.get_value() == 45 + 50 + 30  # 15*3 + 10*5 + 30 = 125
    
    # Make y a quib too
    obj.y = iquib(25)
    
    super2_result = obj.super2_method()
    assert is_quib(super2_result)
    assert super2_result.get_value() == 125  # 25 * 5
    
    sub_result = obj.sub_method()
    assert is_quib(sub_result)
    assert sub_result.get_value() == 45 + 125 + 30  # 15*3 + 25*5 + 30 = 200


def test_dataclass_method_override_stays_quiby():
    @quiby
    @dataclass
    class BaseClass:
        x: int
        
        def calculate(self):
            return self.x * 2
            
        def other_method(self):
            return self.x + 10

    @quiby
    @dataclass  
    class SubClass(BaseClass):
        y: int
        
        def calculate(self):  # Override base method
            return self.x * 3 + self.y
            
        def new_method(self):
            return self.calculate() + self.other_method()

    obj = SubClass(10, 5)
    
    # Check methods are quiby
    assert is_quiby(obj.calculate)
    assert is_quiby(obj.other_method)  # inherited method
    assert is_quiby(obj.new_method)    # new method
    
    # Test with non-quib values
    assert not is_quib(obj.calculate())
    assert not is_quib(obj.other_method())
    assert not is_quib(obj.new_method())
    
    # Verify overridden method works correctly
    assert obj.calculate() == 10 * 3 + 5  # 35
    assert obj.other_method() == 10 + 10   # 20
    assert obj.new_method() == 35 + 20     # 55
    
    # Make x a quib
    obj.x = iquib(15)
    
    # All methods should become quiby since they depend on x
    calc_result = obj.calculate()
    assert is_quib(calc_result)
    assert calc_result.get_value() == 15 * 3 + 5  # 50
    
    other_result = obj.other_method()
    assert is_quib(other_result)
    assert other_result.get_value() == 15 + 10  # 25
    
    new_result = obj.new_method()
    assert is_quib(new_result)
    assert new_result.get_value() == 50 + 25  # 75
    
    # Make y a quib too
    obj.y = iquib(8)
    
    # Overridden method should work with both quibs
    calc_result = obj.calculate()
    assert is_quib(calc_result)
    assert calc_result.get_value() == 15 * 3 + 8  # 53
    
    # other_method only depends on x, so shouldn't change
    assert obj.other_method().get_value() == 15 + 10  # 25
    
    # new_method combines both
    new_result = obj.new_method()
    assert is_quib(new_result)
    assert new_result.get_value() == 53 + 25  # 78


def test_quiby_class_method_bug():
    """Test that class methods work correctly in quiby classes.
    
    Bug was: When an instance method calls a class method via self.class_method(),
    the quiby wrapper incorrectly passed (self, args) instead of (cls, args).
    """
    
    @quiby
    class TestClass:
        @classmethod
        def cls_method(cls, x):
            return x * 2
        
        def call_cls_method(self):
            return self.cls_method(5)  # Should work now
    
    obj = TestClass()
    
    # This should work without throwing TypeError
    result = obj.call_cls_method()
    assert result == 10  # 5 * 2
    
    # Test with quib arguments
    obj.x = iquib(7)
    
    def call_with_quib(self):
        return self.cls_method(self.x)
    
    # Dynamically add method to test with quib args
    TestClass.call_with_quib = quiby(call_with_quib)
    
    result_quib = obj.call_with_quib()
    assert is_quib(result_quib)
    assert result_quib.get_value() == 14  # 7 * 2


def test_unified_quiby_attribute_handling():
    """Test that the unified approach correctly handles all attribute types."""
    
    @quiby
    class UnifiedTest:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        
        # Instance method
        def instance_method(self):
            return self.x + self.y
        
        # Class method
        @classmethod
        def class_method(cls, value):
            return value * 3
        
        # Static method
        @staticmethod
        def static_method(a, b):
            return a - b
        
        # Property
        @property
        def computed_property(self):
            return self.x * self.y
        
        # Method that uses all four types
        def use_all_types(self):
            instance_result = self.instance_method()
            class_result = self.class_method(10)
            static_result = self.static_method(50, 20)
            property_result = self.computed_property
            return instance_result + class_result + static_result + property_result
    
    # Test with regular values
    obj = UnifiedTest(2, 3)
    
    # All should work without quibs
    assert obj.instance_method() == 5      # 2 + 3
    assert obj.class_method(10) == 30      # 10 * 3
    assert obj.static_method(50, 20) == 30 # 50 - 20
    assert obj.computed_property == 6      # 2 * 3
    assert obj.use_all_types() == 71       # 5 + 30 + 30 + 6
    
    # Test with quib values
    obj_quib = UnifiedTest(iquib(4), iquib(5))
    
    # Instance method should return quib
    instance_result = obj_quib.instance_method()
    assert is_quib(instance_result)
    assert instance_result.get_value() == 9  # 4 + 5
    
    # Class method should work normally (no quib args)
    class_result = obj_quib.class_method(10)
    assert not is_quib(class_result)
    assert class_result == 30  # 10 * 3
    
    # Static method should work normally (no quib args)
    static_result = obj_quib.static_method(50, 20)
    assert not is_quib(static_result)
    assert static_result == 30  # 50 - 20
    
    # Property should return quib
    property_result = obj_quib.computed_property
    assert is_quib(property_result)
    assert property_result.get_value() == 20  # 4 * 5
    
    # Combined method should return quib
    combined_result = obj_quib.use_all_types()
    assert is_quib(combined_result)
    assert combined_result.get_value() == 89  # 9 + 30 + 30 + 20


def test_static_method_quibification():
    """Test that static methods are properly quibified."""
    
    @quiby
    class StaticTest:
        @staticmethod
        def add_numbers(a, b):
            return a + b
        
        @staticmethod
        def multiply_numbers(x, y):
            return x * y
    
    obj = StaticTest()
    
    # Test with regular values
    assert obj.add_numbers(2, 3) == 5
    assert StaticTest.add_numbers(2, 3) == 5  # Can call on class too
    
    # Test with quib values
    a_quib = iquib(10)
    b_quib = iquib(20)
    
    # Static method should create quib when called with quib args
    result = obj.add_numbers(a_quib, b_quib)
    assert is_quib(result)
    assert result.get_value() == 30
    
    # Should work when called on class directly too
    result2 = StaticTest.multiply_numbers(a_quib, iquib(3))
    assert is_quib(result2)
    assert result2.get_value() == 30  # 10 * 3
    
    # Changes to quib should propagate
    a_quib.assign(15)
    assert result.get_value() == 35  # 15 + 20
    assert result2.get_value() == 45  # 15 * 3
