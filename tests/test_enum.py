import enum

from pytest import raises

from typedpy import (
    Deserializer,
    Enum,
    ImmutableStructure,
    Integer,
    Map,
    NoneField,
    Positive,
    Serializer,
    String,
    Structure,
    Array,
)


class PositiveEnum(Enum, Positive):
    pass


class B(Structure):
    e = PositiveEnum[23, -5, 12, 5]


def test_not_positive_err():
    with raises(ValueError) as excinfo:
        B(e=-5)
    assert "e: Got -5; Expected a positive number" in str(excinfo.value)


def test_not_valid_value_err():
    with raises(ValueError) as excinfo:
        B(e=10)
    assert "e: Got 10; Expected one of 23, -5, 12, 5" in str(excinfo.value)


def test_valid_value():
    assert B(e=23).e == 23


def test_valid_update():
    b = B(e=23)
    b.e = 12
    assert b.e == 12


def test_within_erray_err():
    class A(Structure):
        arr = Array(items=PositiveEnum(values=[23, -5, 12, 5]))

    with raises(ValueError) as excinfo:
        A(arr=[23, 5, 3, 5])
    assert "arr_2: Got 3; Expected one of 23, -5, 12, 5" in str(excinfo.value)


class Values(enum.Enum):
    ABC = enum.auto()
    DEF = enum.auto()
    GHI = enum.auto()


def test_enum_using_enum():
    class Example(Structure):
        arr = Array[Enum[Values]]

    e = Example(arr=["ABC", Values.DEF, "GHI"])
    assert e.arr == [Values.ABC, Values.DEF, Values.GHI]


def test_enum_using_enum_error():
    class Example(Structure):
        arr = Array[Enum[Values]]

    with raises(ValueError) as excinfo:
        Example(arr=["ABC", Values.DEF, 3])
    assert "Example.arr_2: Got 3; Expected one of: ABC, DEF, GHI" == str(excinfo.value)


def test_enum_using_enum_with_many_values_error():
    class Many(enum.Enum):
        A = 1
        B = 2
        C = 3
        D = 4
        E = 5
        F = 6
        G = 7
        H = 8
        I = 9
        J = 10
        K = 11
        L = 12

    class Example(Structure):
        arr = Array[Enum[Many]]

    with raises(ValueError) as excinfo:
        Example(arr=["A", Many.E, 3])
    assert "arr_2: Got 3; Expected a value of <enum 'Many'>" in str(excinfo.value)


def test_enum_using_enum_values_should_be_the_enum_values():
    def EnumValues():
        return Enum(values=Values)

    class Example(Structure):
        arr = Array[EnumValues()]

    assert EnumValues().values == [Values.ABC, Values.DEF, Values.GHI]
    assert Example.arr.items.values == [Values.ABC, Values.DEF, Values.GHI]


class Many(enum.Enum):
    A = 1
    B = 2
    C = 3
    D = 4


class Example(Structure):
    map = Map[Enum[Many], Integer]
    arr = Array[Enum[Many]]

    _required = []


def test_enum_convert_string_to_enum_value_in_map():
    example = Example(map={"A": 0, "B": 1, "C": 2})
    assert set(example.map.keys()) == {Many.A, Many.B, Many.C}


def test_enum_convert_string_to_enum_value_in_map_serialization():
    serialized = Serializer(Example(map={"A": 0, "B": 1, "C": 2})).serialize()
    deserialized = Deserializer(Example).deserialize(serialized)
    assert set(deserialized.map.keys()) == {Many.A, Many.B, Many.C}


def test_enum_convert_string_to_enum_value_in_array():
    example = Example(arr=["A", "B", "C"])
    assert example.arr == [Many.A, Many.B, Many.C]


def test_enum_convert_string_to_enum_value_in_array_serialization():
    serialized = Serializer(Example(arr=["A", "B", "C"])).serialize()
    deserialized = Deserializer(Example).deserialize(serialized)
    assert deserialized.arr == [Many.A, Many.B, Many.C]


def test_enum_deserialize_by_value():
    class Foo(Structure):
        many: Array[Enum(values=Many, serialization_by_value=True)]
        i: int

    foo = Deserializer(Foo).deserialize({"i": 1, "many": [4, 3, 2, 4]})
    assert foo.many == [Many.D, Many.C, Many.B, Many.D]


def test_enum_serialize_by_value():
    class Foo(Structure):
        many: Array[Enum(values=Many, serialization_by_value=True)]
        i: int

    foo = Foo(i=5, many=[Many.D, Many.C, Many.D, Many.A])
    assert Serializer(foo).serialize() == {"i": 5, "many": [4, 3, 4, 1]}


def test_enum_not_all_values():
    class Many(enum.Enum):
        A = 1
        B = 2
        C = 3
        D = 4
        E = 5
        F = 6

    class Example(Structure):
        arr = Array[Enum(values=[Many.A, Many.B, Many.D])]

    example = Example(arr=["B", Many.A])
    with raises(ValueError) as excinfo:
        example.arr.append(Many.E)
    assert "arr_2: Got Many.E; Expected one of: A, B, D" in str(excinfo.value)


def test_enum_not_all_values_deserialization():
    class Many(enum.Enum):
        A = 1
        B = 2
        C = 3
        D = 4
        E = 5

    class Example(Structure):
        arr = Array[Enum(values=[Many.A, Many.B, Many.D])]

    example = Deserializer(Example).deserialize({"arr": ["A", "D", "D"]})
    assert example.arr[2] == Many.D
    with raises(ValueError) as excinfo:
        Deserializer(Example).deserialize({"arr": ["A", "E", "D"]})
    assert "arr_1: Invalid value: 'E'" == str(excinfo.value)


def test_enum_not_all_values_serialization_by_value():
    class Many(enum.Enum):
        A = 1
        B = 2
        C = 3
        D = 4
        E = 5

    class Example(Structure):
        arr = Array[Enum(values=[Many.A, Many.B, Many.D], serialization_by_value=True)]

    example = Deserializer(Example).deserialize({"arr": [1, 4, 1]})
    assert example.arr[2] == Many.A
    assert Serializer(example).serialize()["arr"] == [1, 4, 1]

    with raises(ValueError) as excinfo:
        Deserializer(Example).deserialize({"arr": ["A"]})
    assert "arr_0: Invalid value: 'A'" in str(excinfo.value)

    with raises(ValueError) as excinfo:
        Deserializer(Example).deserialize({"arr": [1, 4, 2, 3]})
    assert "arr_3: Got Many.C; Expected one of: A, B, D" in str(excinfo.value)


class Method(enum.Enum):
    aaa = 1
    bbb = 2


def test_serialize_optional_given_a_string():
    class Foo(ImmutableStructure):
        pref: NoneField | Enum[Method]

    foo = Foo(pref="aaa")

    assert Serializer(foo).serialize() == {"pref": "aaa"}


def test_serialize_by_value():
    class Foo(enum.Enum):
        A = 1
        B = 2
        C = 3

    class Bar(Structure):
        e: Enum[Foo]
        e_value: Enum(values=Foo, serialization_by_value=True)

        _required = []

    assert Serializer(Bar(e_value=Foo.A)).serialize() == {"e_value": 1}
    assert Serializer(Bar(e=Foo.A)).serialize() == {"e": "A"}
