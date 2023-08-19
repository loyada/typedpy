import sys
from decimal import Decimal

import pytest
from pytest import mark

from typedpy import (
    Array,
    DecimalNumber,
    Deserializer,
    FunctionCall,
    Map,
    Serializer,
    String,
    Structure,
    mappers,
    DoNotSerialize,
)
from typedpy.serialization.mappers import (
    aggregate_deserialization_mappers,
    aggregate_serialization_mappers,
)


def test_aggregated_simple_inheritance():
    class Foo(Structure):
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    mappers_calculated = Bar.get_aggregated_serialization_mapper()
    assert mappers_calculated == [{"i": "j"}, mappers.TO_LOWERCASE]
    assert Deserializer(Bar).deserialize(
        {"J": 5, "A": [1, 2, 3]}, keep_undefined=False
    ) == Bar(i=5, a=[1, 2, 3])


def test_chain_map_and_lowercase():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "B", "s": "S"}
    deserialized = Deserializer(Foo).deserialize({"B": 5, "S": "abc"})
    assert deserialized == Foo(a=5, s="abc")


def test_chain_map_and_lowercase_with_nested():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b.c"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "B.C", "s": "S"}
    deserialized = Deserializer(Foo).deserialize({"B": {"C": 5}, "S": "abc"})
    assert deserialized == Foo(a=5, s="abc")


def test_chain_map_and_camelcase():
    class Foo(Structure):
        a: int
        ssss_ttt: str

        _serialization_mapper = [{"a": "bb_cc"}, mappers.TO_CAMELCASE, {"ssssTtt": "x"}]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "bbCc", "ssss_ttt": "x"}
    deserialized = Deserializer(Foo).deserialize({"bbCc": 5, "x": "abc"})
    assert deserialized == Foo(a=5, ssss_ttt="abc")


def test_aggregated_with_function():
    class Foo(Structure):
        xyz: Array
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    class Blah(Bar):
        s: str
        foo: Foo
        _serialization_mapper = {}
        _deserialization_mapper = {"S": FunctionCall(func=lambda x: x * 2)}

    aggregated = aggregate_deserialization_mappers(Blah)
    assert aggregated == {
        "xyz": "XYZ",
        "i": "J",
        "a": "A",
        "s": FunctionCall(func=Blah._deserialization_mapper["S"].func, args=["S"]),
        "foo": "FOO",
        "FOO._mapper": {"xyz": "XYZ", "i": "J"},
    }

    original = {
        "S": "abc",
        "FOO": {"XYZ": [1, 2], "J": 5},
        "A": [7, 6, 5, 4],
        "XYZ": [1, 4],
        "J": 9,
    }
    deserialized = Deserializer(Blah).deserialize(original, keep_undefined=False)
    assert deserialized == Blah(
        s="abcabc", foo=Foo(i=5, xyz=[1, 2]), xyz=[1, 4], i=9, a=[7, 6, 5, 4]
    )
    serialized = Serializer(deserialized).serialize()
    assert serialized == {**original, "S": "abcabc"}


def test_aggregated_with_function_unsupported():
    class Foo(Structure):
        xyz: Array
        i: int
        _serialization_mapper = {"i": "j"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = mappers.TO_LOWERCASE

    class Blah(Bar):
        s: str
        foo: Foo
        _serialization_mapper = {"S": FunctionCall(func=lambda x: x * 2)}

    blah = Blah(s="abcabc", foo=Foo(i=5, xyz=[1, 2]), xyz=[1, 4], i=9, a=[7, 6, 5, 4])
    with pytest.raises(NotImplementedError) as excinfo:
        Serializer(blah).serialize()
    assert (
        "Combining functions and other mapping in a serialization mapper is unsupported"
        in str(excinfo.value)
    )


def test_chained_mappers():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"a": "B", "s": "S"}
    original = {"B": 5, "S": "xyz"}
    deserialized = Deserializer(Foo).deserialize(original, keep_undefined=False)
    assert deserialized == Foo(a=5, s="xyz")
    serialized = Serializer(deserialized).serialize()
    assert serialized == original


def test_mapper_with_opt():
    class Foo(Structure):
        first = String
        second = String
        opt = String
        _optional = ["opt"]
        _serialization_mapper = mappers.TO_LOWERCASE

    foo: Foo = Deserializer(Foo).deserialize(
        {"FIRST": "ff", "SECOND": "ss", "OPT": "oo"}
    )
    foo2: Foo = Deserializer(Foo).deserialize({"FIRST": "ff", "SECOND": "ss"})
    foo2.opt = foo.opt
    assert foo == foo2


def test_dont_serialize():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": DoNotSerialize}]

    assert Serializer(Foo(a=5, s="xyz")).serialize() == {"s": "xyz"}


def test_dont_serialize_chained():
    class Foo(Structure):
        a: int
        s: str

        _serialization_mapper = [{"a": DoNotSerialize}, mappers.TO_LOWERCASE]

    aggregated = aggregate_deserialization_mappers(Foo)
    assert aggregated == {"s": "S", "a": DoNotSerialize}
    assert Serializer(Foo(a=5, s="xyz")).serialize() == {"S": "xyz"}


def test_dont_serialize_inheritance_chained():
    class Foo(Structure):
        i: int
        s: str
        _serialization_mapper = {"i": "j", "s": "name"}

    class Bar(Foo):
        a: Array

        _serialization_mapper = [{"j": DoNotSerialize}, mappers.TO_LOWERCASE]
        _deserialization_mapper = [mappers.TO_LOWERCASE]

    aggregated = aggregate_serialization_mappers(Bar)
    assert aggregated == {"s": "NAME", "a": "A", "i": DoNotSerialize}
    deserialized = Deserializer(Bar).deserialize(
        {"J": 5, "A": [1, 2, 3], "NAME": "jon"}, keep_undefined=False
    )
    assert deserialized == Bar(i=5, a=[1, 2, 3], s="jon")
    assert Serializer(deserialized).serialize() == {"NAME": "jon", "A": [1, 2, 3]}


def test_chained_mappers_with_additional_serialization_props():
    class Foo(Structure):
        a: int
        s: str

        x = 1

        def double_a(self):
            return self.a * 2

        _serialization_mapper = [{"a": "b"}, mappers.TO_LOWERCASE]

        def _additional_serialization(self) -> dict:
            return {
                "double_a": self.double_a,
                "x": self.x,
                "triple_a": self.a * 3,
                "y": [1, 2, 3],
                "z": lambda: Foo.x + self.a,
            }

    original = {"B": 5, "S": "xyz"}
    deserialized = Deserializer(Foo).deserialize(original, keep_undefined=False)
    assert deserialized == Foo(a=5, s="xyz")
    serialized = Serializer(deserialized).serialize()
    assert serialized == {
        **original,
        "double_a": 10,
        "x": 1,
        "triple_a": 15,
        "y": [1, 2, 3],
        "z": 6,
    }


def test_additional_serialization_props():
    class Purchase(Structure):
        amount_by_product: Map[str, int]
        commission = 10

        def purchase_total(self):
            return sum(self.amount_by_product.values()) + self.commission

        def _additional_serialization(self):
            return {
                "commission": Purchase.commission,
                "purchase_total": self.purchase_total,
            }

    amount_by_product = {"a": 50, "b": 30}
    purchase = Purchase(amount_by_product=amount_by_product)
    serialized = Serializer(purchase).serialize()
    assert serialized == {
        "amount_by_product": amount_by_product,
        "commission": 10,
        "purchase_total": 90,
    }


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_defect_in_complex_mapper1():
    class Blah(Structure):
        amount: DecimalNumber

        _deserialization_mapper = [
            {"amount": "amount_decimal"},
            {"amount_decimal": FunctionCall(func=lambda x: Decimal(x) * 2)},
        ]
        _required = []

    class Foo(Structure):  # noqa
        blah: Blah
        i: int

        _required = []

    class FooList(Structure):
        foos: list[Foo]

    assert Deserializer(FooList).deserialize(
        {"foos": [{"i": 5}]}, keep_undefined=False
    ) == FooList(foos=[Foo(i=5)])


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_defect_in_complex_mapper2():
    class Blah(Structure):
        amount: DecimalNumber

        _serialization_mapper = [
            {
                "amount": FunctionCall(
                    func=lambda x: Decimal(x) * 2, args=["amount_decimal"]
                )
            },
        ]
        _required = []

    class Foo(Structure):  # noqa
        blah: Blah
        i: int

        _required = []

    class FooList(Structure):
        foos: list[Foo]

    deserialized = Deserializer(FooList).deserialize(
        {
            "foos": [
                {"i": 5},
                {"i": 4, "blah": {}},
                {"i": 3, "blah": {"amount_decimal": "5"}},
            ]
        },
        keep_undefined=False,
    )
    assert deserialized == FooList(
        foos=[Foo(i=5), Foo(i=4, blah=Blah()), Foo(i=3, blah=Blah(amount=Decimal(10)))]
    )


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_defect_in_complex_mapper3():
    class Blah(Structure):
        amount: DecimalNumber

        _serialization_mapper = [
            {
                "amount": FunctionCall(
                    func=lambda x: Decimal(x) * 2, args=["amount_decimal"]
                )
            },
        ]
        _required = []

    class Foo(Structure):
        blas: list[Blah]

    assert Deserializer(Foo).deserialize({"blas": [{}]}, keep_undefined=False) == Foo(
        blas=[Blah()]
    )


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_serialization_mapper_inheritance1():
    class Foo(Structure):
        current_level: int
        _serialization_mapper = mappers.TO_CAMELCASE

    class Bar(Foo):
        sub_categories: list[Foo]
        number_of_transactions: int
        _required = ["current_level"]
        _serialization_mapper = mappers.TO_CAMELCASE

    a = Bar(
        current_level=1,
        number_of_transactions=2,
        sub_categories=[
            Bar(
                current_level=2,
                number_of_transactions=2,
                sub_categories=[Bar(current_level=3, number_of_transactions=1)],
            )
        ],
    )
    serialized = Serializer(a).serialize()

    assert serialized == {
        "currentLevel": 1,
        "numberOfTransactions": 2,
        "subCategories": [
            {
                "currentLevel": 2,
                "numberOfTransactions": 2,
                "subCategories": [{"currentLevel": 3, "numberOfTransactions": 1}],
            }
        ],
    }


@mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_serialization_mapper_inheritance2():
    class Foo(Structure):
        current_level: int

    class Bar(Foo):
        sub_categories: list[Foo]
        number_of_transactions: int
        _required = ["current_level"]
        _serialization_mapper = mappers.TO_CAMELCASE

    a = Bar(
        current_level=1,
        number_of_transactions=2,
        sub_categories=[
            Bar(
                current_level=2,
                number_of_transactions=2,
                sub_categories=[Bar(current_level=3, number_of_transactions=1)],
            )
        ],
    )
    serialized = Serializer(a).serialize()

    assert serialized == {
        "currentLevel": 1,
        "numberOfTransactions": 2,
        "subCategories": [
            {
                "currentLevel": 2,
                "numberOfTransactions": 2,
                "subCategories": [{"currentLevel": 3, "numberOfTransactions": 1}],
            }
        ],
    }
