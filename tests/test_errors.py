import json

from typedpy import DateField
from typedpy import (
    Structure,
    DecimalNumber,
    String,
    Array,
    standard_readable_error_for_typedpy_exception,
    Positive,
    deserialize_structure,
    Integer,
    AnyOf,
    AllOf,
    OneOf,
    Float,
    StructureReference,
    Number,
    Enum,
    Anything,
)

from pytest import raises, fixture

from typedpy.errors import ErrorInfo, get_simplified_error


class PositiveDecimal(DecimalNumber, Positive):
    pass


class Foo(Structure):
    a = DecimalNumber
    b = DecimalNumber(maximum=100, multiplesOf=5)
    c = PositiveDecimal
    d = DateField
    arr = Array(items=String, minItems=1)
    _optional = ["d"]
    _additionalProperties = False


def test_error_1():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1, arr=["abc", 1])
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo.arr_1", problem="Expected a string", value="1"
    )


def test_error_2():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1, arr=2)
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo.arr", problem="Expected an array", value="2"
    )


def test_error_3():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1)
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo", problem="missing a required argument: 'arr'"
    )


def test_error_4():
    with raises(Exception) as ex:
        Foo(a=1, b=10, c=1.1, arr=[])
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo.arr", problem="Expected length of at least 1", value="[]"
    )


def test_error_5():
    with raises(Exception) as ex:
        Foo(a=1, b=1000, c=1.1, arr=["a"])
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo.b", problem="Expected a maximum of 100", value="1000"
    )


def test_error_6():
    with raises(Exception) as ex:
        Foo(a=1, b=100, c=1.1, arr=["a"], d="xyz")
    print(standard_readable_error_for_typedpy_exception(ex.value))
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo.d",
        problem="time data 'xyz' does not match format '%Y-%m-%d'",
        value="'xyz'",
    )


def test_error_7():
    with raises(Exception) as ex:
        Foo(a=1, b=100, c=1.1, arr=["a"], e=5)
    assert standard_readable_error_for_typedpy_exception(ex.value) == ErrorInfo(
        field="Foo", problem="got an unexpected keyword argument 'e'"
    )


def test_real_world_usage():
    try:
        Foo(a=1, b=10, c=1.1, arr=["abc", 1])
    except Exception as ex:
        assert standard_readable_error_for_typedpy_exception(ex) == ErrorInfo(
            field="Foo.arr_1", problem="Expected a string", value="1"
        )


@fixture(name="all_errors")
def fixture_all_errors():
    Structure.set_fail_fast(False)
    yield
    Structure.set_fail_fast(True)


def test_multiple_errors_not_fail_fast(all_errors):
    with raises(Exception) as ex:
        Foo(a=1, b=1000, c=-5, arr=[1])
    errs = standard_readable_error_for_typedpy_exception(ex.value)
    assert (
        ErrorInfo(field="Foo.b", problem="Expected a maximum of 100", value="1000")
        in errs
    )
    assert ErrorInfo(field="Foo.arr_0", problem="Expected a string", value="1") in errs
    assert (
        ErrorInfo(field="Foo.c", problem="Expected a positive number", value="-5")
        in errs
    )
    simple_form = json.loads(str(ex.value))
    assert set(simple_form) == {
        "Foo.b: Got 1000; Expected a maximum of 100",
        "Foo.arr_0: Got 1; Expected a string",
        "Foo.c: Got -5; Expected a positive number",
    }


###############################################################################################


class SimpleStruct(Structure):
    name = String(pattern="[A-Za-z]+$", maxLength=8)


class Person(Structure):
    name = String
    ssid = String(minLength=3)


class BigPerson(Person):
    height = Integer
    _required = []


class Example(Structure):
    anything = Anything
    i = Integer(maximum=10)
    s = String(maxLength=5)
    any = AnyOf[Array[Person], Person]
    complex_allof = AllOf[
        AnyOf[Integer, Person], BigPerson
    ]  # this is stupid, but we do it for testing
    people = Array[Person]
    array_of_one_of = Array[
        OneOf[Float, Integer, Person, StructureReference(a1=Integer(), a2=Float())]
    ]
    array = Array[Integer(multiplesOf=5), OneOf[Array[Person], Number]]
    embedded = StructureReference(a1=Integer(), a2=Float())
    simplestruct = SimpleStruct
    all = AllOf[Number, Integer]
    enum = Enum(values=[1, 2, 3])
    _required = []


"""
    complex test that tests many variations of fields, including various multi-field
"""


def test_unsuccessful_deserialization_with_many_types(all_errors):
    data = {
        "anything": {"a", "b", "c"},
        "i": 50,  # Error: > 10
        "s": [],  # Error: should be string
        "complex_allof": {"name": "john", "ssid": "123"},
        "array": [10, 7, "aaa"],  # Error: array_2
        "any": [{"name": "john", "ssid": "123"}, "xxx"],  # any_1
        "embedded": {
            "a1": 8,
            #         'a2': 0.5         # Error: missing 'a2'
        },
        "people": [{"name": "john", "ssid": "13"}],
        "simplestruct": {"name": "danny"},
        "array_of_one_of": [
            {"a1": 8, "a2": 0.5},
            0.5,
            4,
            {"name": "john", "ssid": "123"},
        ],
        "all": 5,
        "enum": 4,  # Error
    }

    with raises(Exception) as ex:
        deserialize_structure(Example, data)
    errs = standard_readable_error_for_typedpy_exception(ex.value)
    expected_errors = [
        ErrorInfo(field="Example.i", problem="Expected a maximum of 10", value="50"),
        ErrorInfo(field="Example.s", problem="Expected a string", value="[]"),
        ErrorInfo(
            field="Example.any",
            problem="Does not match any field option:"
            " (1) Does not match <Array. Properties: items = <ClassReference: Person>>. reason: any_1: Expected "
            "a dictionary; Got 'xxx'. (2) Does not match <ClassReference: Person>."
            " reason: any: Expected a dictionary; Got"
            " [{'name': 'john', 'ssid': '123'}, 'xxx']",
            value="[{'name': 'john', 'ssid': '123'}, 'xxx']",
        ),
        ErrorInfo(field="Example.enum", problem="Expected one of 1, 2, 3", value="4"),
        ErrorInfo(
            field="Example.people_0",
            problem=[
                ErrorInfo(
                    field="Person.ssid",
                    problem="Expected a minimum length of 3",
                    value="'13'",
                )
            ],
        ),
        ErrorInfo(
            field="Example.embedded",
            problem="StructureReference_1: missing a required argument: 'a2'",
            value="{'a1': 8}",
        ),
    ]
    for e in expected_errors[:-1]:
        print(e)
        assert e in errs
    simple_form = get_simplified_error(str(ex.value))
    for e in simple_form:
        if "StructureReference" not in e:
            assert e in {
                "Example.i: Got 50; Expected a maximum of 10",
                "Example.s: Got []; Expected a string",
                "Example.any: Got [{'name': 'john', 'ssid': '123'}, 'xxx']; Does not match any field option: (1) Does not match <Array. Properties: items = <ClassReference: Person>>. reason: any_1: Expected a dictionary; Got 'xxx'. (2) Does not match <ClassReference: Person>. reason: any: Expected a dictionary; Got [{'name': 'john', 'ssid': '123'}, 'xxx']",
                "Example.people_0: Person.ssid: Got '13'; Expected a minimum length of 3",
                "Example.embedded: Got {'a1': 8}; StructureReference_1: missing a required argument: 'a2'",
                "Example.enum: Got 4; Expected one of 1, 2, 3",
            }

    expected = expected_errors[-1]
    for e in errs:
        if e.field == expected.field and e.value == expected.value:
            return
    assert False


def test_simplified_form1(all_errors):
    err1 = "a: got foo; expected bar"
    err1_wrapped = json.dumps([err1])
    err2 = f"b:{err1_wrapped}"
    err2_wrapped = json.dumps([err2])
    err3 = f"c: {err2_wrapped}"
    err3_wrapped = json.dumps([err3])

    simple_form = get_simplified_error(err3_wrapped)

    assert simple_form == ["c: b: a: got foo; expected bar"]


def test_missed_required(all_errors):
    class Foo(Structure):
        r: str

    with raises(Exception) as ex:
        deserialize_structure(Foo, {})
    errs = standard_readable_error_for_typedpy_exception(ex.value)
    assert errs[0].problem.startswith("missing a required argument: 'r'")


def test_string_err_wrapper(all_errors):
    class Foo(Structure):
        a: String(pattern=r"[\d]{3}")

    #   b: String(pattern="[\\d]{5}")

    class Bar(Structure):
        foos: Array[Foo]

    with raises(ValueError) as ex:
        Bar(foos=[Foo(a="a")])
    simple_form = get_simplified_error(str(ex.value))
    assert simple_form == [
        """Foo.a: Got 'a'; Does not match regular expression: '[\d]{3}'"""
    ]
