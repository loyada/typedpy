from examples import Foo
from examples.enums import State
from typedpy import Enum, Extend, ImmutableStructure, Partial, PositiveInt, String, create_pyi


class Vehicle(ImmutableStructure):
    license_plate: str
    license_plate_state = Enum[State]
    odometer = PositiveInt()
    alias = String


class AnotherFoo(Extend[Foo]):
    another: str


class Vehicle2(Partial[Vehicle], ImmutableStructure):
    pass

if __name__ == "__main__":
    create_pyi(__file__, locals())
