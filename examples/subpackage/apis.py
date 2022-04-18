from examples.enums import State
from typedpy import Enum, ImmutableStructure, PositiveInt, String, create_pyi


class Vehicle(ImmutableStructure):
    license_plate: str
    license_plate_state = Enum[State]
    odometer = PositiveInt()
    alias = String


if __name__ == "__main__":
    create_pyi(__file__, locals())
